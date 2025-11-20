#!/usr/bin/env python3
"""
Web Scraper REST API
Advanced web scraping API with Playwright integration

Author: Volkan AYDIN
Year: 2025
License: CC BY-NC-SA 4.0 (Non-Commercial)

Features:
- Unified scraping API with 'get' and 'collect' operations
- Advanced CSS selector syntax with parent navigation
- Attribute extraction support
- Proxy integration
- Screenshot capabilities
- Debug mode with HTML output

Support this project:
- Bitcoin: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh
- Commercial license: volkan@designmonkeys.net
"""

import os
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
import asyncio
import json
import logging
from typing import Optional, Union, Dict, List, Any, Tuple
from scraper import WebScraper
import time
import uuid
import re
import base64
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API Keys (load from environment variables for security)
VALID_API_KEYS = os.getenv('VALID_API_KEYS', 'sk-demo-key-12345').split(',')

# Lifespan event handler
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    logger.info("🚀 Starting Web Scraper API...")
    yield
    # Shutdown
    logger.info("🛑 Shutting down Web Scraper API...")
    for scraper in scraper_pool:
        await scraper.close()
    scraper_pool.clear()

# FastAPI app
app = FastAPI(
    title="Web Scraper API",
    description="REST API for web scraping with proxy support - POST methods only. Supports both HTML source extraction and advanced element scraping.",
    version="1.0.0",
    lifespan=lifespan
)

# Unified scraping models
class UnifiedScrapeRequest(BaseModel):
    url: HttpUrl
    use_proxy: bool = True
    proxy_url: Optional[str] = None
    wait_time: int = 3
    wait_for_element: bool = False
    element_timeout: int = 30
    debug: bool = False
    take_screenshot: bool = False
    extract_links: bool = False
    click: Optional[List[str]] = None  # Array of CSS selectors to click in sequence
    get: Optional[Dict[str, Union[str, Dict[str, Any]]]] = None
    collect: Optional[Dict[str, Dict[str, Any]]] = None

class UnifiedScrapeResponse(BaseModel):
    success: bool
    url: str
    data: Dict[str, Any]
    load_time: float
    timestamp: str
    error: Optional[str] = None
    debug_html: str = ""
    screenshot_path: Optional[str] = None
    links: Optional[List[str]] = None

# Request/Response models
class ScrapeRequest(BaseModel):
    url: HttpUrl
    use_proxy: bool = False
    proxy_url: Optional[str] = None
    wait_time: int = 3
    take_screenshot: bool = False
    extract_text: bool = True
    extract_links: bool = False
    extract_images: bool = False

class ScrapeResponse(BaseModel):
    success: bool
    url: str
    status_code: int
    content_length: int
    html_content: str
    text_content: Optional[str] = None
    links: Optional[list] = None
    images: Optional[list] = None
    screenshot_path: Optional[str] = None
    proxy_used: Optional[str] = None
    ip_address: Optional[str] = None
    load_time: float
    timestamp: str
    error: Optional[str] = None

# New CSS Selector models
class FieldSelector(BaseModel):
    selector: str
    attr: Optional[str] = None

class SelectorScrapeRequest(BaseModel):
    url: HttpUrl
    selector: str
    collection: bool = False
    attr: Optional[str] = None  # For single element attribute extraction
    fields: Optional[Dict[str, Union[str, FieldSelector]]] = None  # For collection field extraction
    use_proxy: bool = True  # Default to True for proxy usage
    proxy_url: Optional[str] = None
    wait_time: int = 3
    wait_for_element: bool = False  # Wait for element to appear
    element_timeout: int = 30  # Timeout for element waiting (seconds)
    debug: bool = False  # Return page HTML for debugging
    include_html: bool = False  # Include HTML content along with text

class SelectorScrapeResponse(BaseModel):
    success: bool
    url: str
    data: Any  # Accept any type of data (string, list, dict, etc.)
    load_time: float
    timestamp: str
    error: Optional[str] = None
    debug_html: str = ""  # Page HTML for debugging

# Authentication dependency
async def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key from header"""
    if not x_api_key:
        raise HTTPException(
            status_code=401, 
            detail="API key required. Add 'X-API-Key' header"
        )
    
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return x_api_key

# Scraper pool
scraper_pool = []

async def get_scraper():
    """Get scraper from pool or create new one with robust error handling"""
    import random
    
    scraper = None
    try:
        # Create new scraper for IP rotation
        scraper = WebScraper()
        
        # Set random proxy index for rotation
        if scraper.proxy_list:
            scraper.current_proxy_index = random.randint(0, len(scraper.proxy_list) - 1)
            logger.info(f"🎲 Random proxy selected: index {scraper.current_proxy_index}")
        
        await scraper.setup_browser()
        return scraper
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Error creating scraper: {e}")
        # Cleanup if scraper was created but setup failed
        if scraper:
            try:
                await cleanup_scraper(scraper)
            except:
                pass
        raise

async def cleanup_scraper(scraper: WebScraper):
    """Cleanup scraper resources with robust error handling"""
    if not scraper:
        return
    
    try:
        # Set a maximum timeout for cleanup (30 seconds)
        await asyncio.wait_for(scraper.close(), timeout=30.0)
    except asyncio.TimeoutError:
        logger.error("❌ Cleanup timeout - browser resources may not be fully released")
        # Force cleanup by setting resources to None
        try:
            scraper.page = None
            scraper.context = None
            scraper.browser = None
            if hasattr(scraper, 'playwright'):
                scraper.playwright = None
        except:
            pass
    except Exception as e:
        error_msg = str(e)
        # EPIPE errors are expected when browser process already terminated
        if 'EPIPE' not in error_msg and 'broken pipe' not in error_msg.lower():
            logger.error(f"❌ Cleanup error: {e}")
        else:
            logger.debug(f"Cleanup EPIPE error (expected): {e}")
        # Ensure resources are cleaned up even on error
        try:
            scraper.page = None
            scraper.context = None
            scraper.browser = None
            if hasattr(scraper, 'playwright'):
                scraper.playwright = None
        except:
            pass
    finally:
        # Don't remove from pool since we're not using pool anymore
        pass

@app.post("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Web Scraper API",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/scrape",
            "/proxies",
            "/test-proxy"
        ]
    }

@app.post("/health")
async def health_check(api_key: str = Depends(verify_api_key)):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "scraper_pool_size": len(scraper_pool),
        "api_key": api_key[:20] + "..."
    }

def clean_text(text: str) -> str:
    """Clean text by removing excessive whitespace"""
    if not text:
        return ""
    # Replace all whitespace characters (tabs, newlines, spaces) with single space
    cleaned = re.sub(r'[\t\n\r\s]+', ' ', text)
    # Remove leading/trailing spaces
    return cleaned.strip()

async def get_image_from_browser(scraper: WebScraper, selector: str, max_size_mb: float = 5.0) -> Optional[str]:
    """
    Get image data directly from browser (already loaded by Playwright)
    
    Args:
        scraper: WebScraper instance with browser context
        selector: CSS selector for the image element
        max_size_mb: Maximum size limit in MB
    
    Returns:
        Base64 encoded image data or None if failed
    """
    try:
        logger.info(f"🖼️ Extracting image from browser: {selector}")
        
        # Get image data directly from browser using canvas
        base64_data = await scraper.page.evaluate(f"""
            async () => {{
                const img = document.querySelector('{selector}');
                if (!img) {{
                    console.log('Image element not found');
                    return null;
                }}
                
                // Wait for image to load
                if (!img.complete) {{
                    await new Promise(resolve => {{
                        img.onload = resolve;
                        img.onerror = resolve;
                    }});
                }}
                
                if (!img.complete || img.naturalWidth === 0) {{
                    console.log('Image not loaded properly');
                    return null;
                }}
                
                // Create canvas to get image data
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                canvas.width = img.naturalWidth;
                canvas.height = img.naturalHeight;
                
                ctx.drawImage(img, 0, 0);
                
                // Convert to base64
                const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
                
                // Check size (approximate)
                const sizeBytes = (dataUrl.length * 3) / 4;
                const sizeMB = sizeBytes / (1024 * 1024);
                
                if (sizeMB > {max_size_mb}) {{
                    console.log('Image too large:', sizeMB.toFixed(2), 'MB');
                    return null;
                }}
                
                return dataUrl;
            }}
        """)
        
        if base64_data:
            # Extract size info for logging
            size_bytes = (len(base64_data) * 3) / 4
            size_mb = size_bytes / (1024 * 1024)
            logger.info(f"✅ Image extracted from browser: {size_mb:.2f}MB")
            return base64_data
        else:
            logger.warning(f"⚠️ Failed to extract image from browser")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error extracting image from browser: {e}")
        return None

async def download_image_binary(scraper: WebScraper, image_url: str, max_size_mb: float = 5.0) -> Optional[str]:
    """
    Download image and return as base64 encoded string (fallback method)
    
    Args:
        scraper: WebScraper instance with browser context
        image_url: URL of the image to download
        max_size_mb: Maximum size in MB (default: 5MB)
    
    Returns:
        Base64 encoded image data or None if failed
    """
    try:
        logger.info(f"🖼️ Downloading image: {image_url}")
        
        # Use browser context to download image (respects proxy settings)
        response = await scraper.page.request.get(image_url)
        
        if response.status != 200:
            logger.error(f"❌ Failed to download image: HTTP {response.status}")
            return None
        
        # Get content type
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            logger.warning(f"⚠️ Content type is not an image: {content_type}")
            return None
        
        # Get content length
        content_length = response.headers.get('content-length')
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            if size_mb > max_size_mb:
                logger.warning(f"⚠️ Image too large: {size_mb:.2f}MB > {max_size_mb}MB")
                return None
        
        # Get binary data
        image_data = await response.body()
        
        # Check size after download
        size_mb = len(image_data) / (1024 * 1024)
        if size_mb > max_size_mb:
            logger.warning(f"⚠️ Image too large after download: {size_mb:.2f}MB > {max_size_mb}MB")
            return None
        
        # Encode to base64
        base64_data = base64.b64encode(image_data).decode('utf-8')
        
        # Create data URL
        data_url = f"data:{content_type};base64,{base64_data}"
        
        logger.info(f"✅ Image downloaded successfully: {size_mb:.2f}MB, type: {content_type}")
        return data_url
        
    except Exception as e:
        logger.error(f"❌ Error downloading image {image_url}: {str(e)}")
        return None

def parse_selector_and_attr(selector_str: str) -> Tuple[str, Optional[str]]:
    """Parse selector and attribute from notation like 'a(href)', 'img(src)', '>> a(href)', '* a(href)', '.child<div<div>h1'"""
    if '(' in selector_str and selector_str.endswith(')'):
        # Find the last opening parenthesis to handle nested selectors
        last_open = selector_str.rfind('(')
        selector = selector_str[:last_open]
        attr = selector_str[last_open+1:selector_str.find(')', last_open)]
        return selector.strip(), attr.strip()
    else:
        # No attribute specified, return selector as is
        return selector_str.strip(), None

def parse_query_builder_selector(selector: str) -> Tuple[List[str], List[str]]:
    """
    Parse query builder selector into selections and operators
    
    Example: "a.test<.product_pod<section>div.alert>strong"
    Returns: 
        selections: ["a.test", ".product_pod", "section", "div.alert", "strong"]
        operators: ["<", "<", ">", ">"]
    """
    import re
    
    # Split by operators <, >, + and spaces
    # Use regex to split while keeping the operators
    parts = re.split(r'([<>+\s]+)', selector)
    
    # Filter out empty strings and clean up
    parts = [part.strip() for part in parts if part.strip()]
    
    selections = []
    operators = []
    
    for i, part in enumerate(parts):
        if part in ['<', '>', '+']:
            operators.append(part)
        elif part not in [' ', '\t', '\n']:
            selections.append(part)
    
    logger.info(f"🔧 Query Builder Parse: selections={selections}, operators={operators}")
    return selections, operators

async def execute_query_builder(scraper: WebScraper, selections: List[str], operators: List[str], 
                               operation_type: str = "single", attr: Optional[str] = None) -> Union[str, List[str]]:
    """
    Execute query builder algorithm
    
    Algorithm:
    1. Start with first selection: document.querySelector(selections[0])
    2. For each operator:
       - If '<': use closest(selections[i+1])
       - If '>': use querySelector(selections[i+1])
       - If '+': use nextElementSibling then querySelector(selections[i+1])
    3. Return final result
    """
    if not selections:
        return "" if operation_type == "single" else []
    
    # Build JavaScript code for query builder
    js_steps = []
    
    if operation_type == "single":
        # Single element extraction
        js_steps.append(f"let currentElement = document.querySelector('{selections[0]}');")
        js_steps.append("console.log('Initial element:', currentElement);")
        js_steps.append("if (!currentElement) return null;")
        
        # Process each operator and next selection
        for i, operator in enumerate(operators):
            if i + 1 >= len(selections):
                break
                
            next_selection = selections[i + 1]
            
            if operator == '<':
                # Parent navigation: closest()
                js_steps.append(f"currentElement = currentElement.closest('{next_selection}');")
                js_steps.append(f"console.log('After closest({next_selection}):', currentElement);")
            elif operator == '>':
                # Child navigation: querySelector()
                js_steps.append(f"currentElement = currentElement.querySelector('{next_selection}');")
                js_steps.append(f"console.log('After querySelector({next_selection}):', currentElement);")
            elif operator == '+':
                # Sibling navigation: nextElementSibling then querySelector()
                js_steps.append("currentElement = currentElement.nextElementSibling;")
                js_steps.append("console.log('After nextElementSibling:', currentElement);")
                js_steps.append(f"if (currentElement) currentElement = currentElement.querySelector('{next_selection}');")
                js_steps.append(f"console.log('After sibling querySelector({next_selection}):', currentElement);")
            
            js_steps.append("if (!currentElement) return null;")
        
        # Final result extraction for single element
        if attr:
            js_steps.append(f"return currentElement ? currentElement.getAttribute('{attr}') || '' : '';")
        else:
            js_steps.append("return currentElement ? (currentElement.innerText || currentElement.textContent || '') : '';")
    
    else:
        # Collection extraction
        js_steps.append(f"const elements = document.querySelectorAll('{selections[0]}');")
        js_steps.append("console.log('Found elements:', elements.length);")
        js_steps.append("const results = [];")
        js_steps.append("for (let i = 0; i < elements.length; i++) {")
        js_steps.append("    let currentElement = elements[i];")
        js_steps.append("    console.log('Processing element:', i, currentElement);")
        
        # Process each operator and next selection for each element
        for i, operator in enumerate(operators):
            if i + 1 >= len(selections):
                break
                
            next_selection = selections[i + 1]
            
            if operator == '<':
                # Parent navigation: closest()
                js_steps.append(f"    currentElement = currentElement.closest('{next_selection}');")
                js_steps.append(f"    console.log('After closest({next_selection}):', currentElement);")
            elif operator == '>':
                # Child navigation: querySelector()
                js_steps.append(f"    currentElement = currentElement.querySelector('{next_selection}');")
                js_steps.append(f"    console.log('After querySelector({next_selection}):', currentElement);")
            elif operator == '+':
                # Sibling navigation: nextElementSibling then querySelector()
                js_steps.append("    currentElement = currentElement.nextElementSibling;")
                js_steps.append("    console.log('After nextElementSibling:', currentElement);")
                js_steps.append(f"    if (currentElement) currentElement = currentElement.querySelector('{next_selection}');")
                js_steps.append(f"    console.log('After sibling querySelector({next_selection}):', currentElement);")
            
            js_steps.append("    if (!currentElement) break;")
        
        # Final result extraction for collection
        if attr:
            js_steps.append(f"    const result = currentElement ? currentElement.getAttribute('{attr}') || '' : '';")
        else:
            js_steps.append("    const result = currentElement ? (currentElement.innerText || currentElement.textContent || '') : '';")
        
        js_steps.append("    results.push(result);")
        js_steps.append("}")
        js_steps.append("return results;")
    
    js_code = '\n'.join(js_steps)
    logger.info(f"🔧 Query Builder JavaScript: {js_code}")
    
    # Execute JavaScript
    result = await scraper.page.evaluate(f"""
        () => {{
            {js_code}
        }}
    """)
    
    if operation_type == "single":
        return clean_text(result) if result else ""
    else:
        return [clean_text(item) for item in result] if result else []

async def unified_parser(scraper: WebScraper, selector: str, operation_type: str = "single", 
                        attr: Optional[str] = None, fields: Optional[Dict[str, Union[str, FieldSelector]]] = None,
                        include_html: bool = False, debug: bool = False) -> Union[str, List[str], List[Dict[str, Any]], Dict[str, str]]:
    """
    Unified parser function that handles all types of element extraction
    
    Args:
        scraper: WebScraper instance
        selector: CSS selector string
        operation_type: "single" for single element, "collection" for multiple elements
        attr: Attribute name to extract (e.g., "href", "src")
        fields: Dictionary of field configurations for collection extraction
        include_html: Whether to include HTML content along with text
    
    Returns:
        Extracted data based on operation type and parameters
    """
    logger.info(f"🔍 Unified parser called: selector='{selector}', type='{operation_type}', attr='{attr}'")
    
    # Parse selector and attribute if not explicitly provided
    if not attr and '(' in selector and selector.endswith(')'):
        parsed_selector, attr = parse_selector_and_attr(selector)
    else:
        parsed_selector = selector
    
    # Handle query builder syntax (<, >, + operators)
    if any(op in parsed_selector for op in ['<', '>', '+']):
        logger.info("🔧 Query builder syntax detected")
        selections, operators = parse_query_builder_selector(parsed_selector)
        return await execute_query_builder(scraper, selections, operators, operation_type, attr)
    
    # Special handling for img elements without attr - return binary data
    logger.info(f"🔍 Checking img detection: selector='{parsed_selector}', ends_with_img={parsed_selector.lower().strip().endswith('img')}, attr='{attr}'")
    if parsed_selector.lower().strip().endswith('img') and not attr:
        logger.info("🖼️ Image element detected without attribute - extracting binary data")
        return await extract_single_image_binary(scraper, parsed_selector)
    
    # Single element extraction
    if operation_type == "single":
        if attr:
            # Extract attribute
            return await extract_single_attribute(scraper, parsed_selector, attr)
        elif include_html:
            # Extract both text and HTML
            return await extract_single_text_and_html(scraper, parsed_selector)
        else:
            # Extract text only
            return await extract_single_text(scraper, parsed_selector)
    
    # Collection extraction
    elif operation_type == "collection":
        # Special handling for img elements in collection without attr - return binary data
        if parsed_selector.lower().strip().endswith('img') and not attr:
            logger.info("🖼️ Image collection detected without attribute - extracting binary data")
            return await extract_collection_images_binary(scraper, parsed_selector)
        
        if fields:
            # Extract with multiple fields
            return await extract_collection_with_fields(scraper, parsed_selector, fields, debug=debug)
        elif attr:
            # Extract attributes from multiple elements
            return await extract_collection_attributes(scraper, parsed_selector, attr)
        elif include_html:
            # Extract both text and HTML from multiple elements
            return await extract_collection_text_and_html(scraper, parsed_selector)
        else:
            # Extract text from multiple elements
            return await extract_collection_text(scraper, parsed_selector)
    
    else:
        raise ValueError(f"Invalid operation_type: {operation_type}")



async def extract_single_text(scraper: WebScraper, selector: str) -> str:
    """Extract text from single element"""
    logger.info(f"🔍 extract_single_text called with: {selector}")
    
    # For debugging - return debug info in result
    if selector == ".child<div<div>h1":
        return f"DEBUG: Original selector '{selector}' received"
    
    # Parse selector and attribute
    parsed_selector, attr = parse_selector_and_attr(selector)
    logger.info(f"🔍 parsed_selector: '{parsed_selector}', attr: '{attr}'")
    
    # Check if this is an img element for binary extraction
    if parsed_selector.lower().strip().endswith('img') and not attr:
        logger.info("🖼️ Image element detected in extract_single_text - extracting binary data")
        return await extract_single_image_binary(scraper, parsed_selector)
    
    if attr:
        # Extract attribute value
        logger.info("🔍 Extracting attribute")
        return await extract_single_attribute(scraper, parsed_selector, attr)
    else:
        # Check if this is a query builder syntax with <, >, +
        if any(op in parsed_selector for op in ['<', '>', '+']):
            logger.info("🔧 Found query builder syntax, using query builder")
            selections, operators = parse_query_builder_selector(parsed_selector)
            return await execute_query_builder(scraper, selections, operators, "single", attr)
        else:
            logger.info("🔍 Normal selector extraction")
            # Extract text content
            text = await scraper.page.evaluate(f"""
                () => {{
                    const element = document.querySelector('{parsed_selector}');
                    if (!element) return '';
                    return element.innerText || element.textContent || '';
                }}
            """) or ""
            # Clean up whitespace in Python
            return clean_text(text)



async def extract_single_html(scraper: WebScraper, selector: str) -> str:
    """Extract HTML content from single element"""
    return await scraper.page.evaluate(f"""
        () => {{
            const element = document.querySelector('{selector}');
            return element ? element.outerHTML : '';
        }}
    """) or ""

async def extract_single_text_and_html(scraper: WebScraper, selector: str) -> Dict[str, str]:
    """Extract both text and HTML from single element"""
    result = await scraper.page.evaluate(f"""
        () => {{
            const element = document.querySelector('{selector}');
            if (!element) return {{ text: '', html: '' }};
            return {{
                text: element.innerText || element.textContent || '',
                html: element.outerHTML
            }};
        }}
    """)
    if result:
        result['text'] = clean_text(result['text'])
    return result or {"text": "", "html": ""}

async def extract_single_attribute(scraper: WebScraper, selector: str, attr: str) -> str:
    """Extract attribute from single element"""
    return await scraper.page.evaluate(f"""
        () => {{
            const element = document.querySelector('{selector}');
            return element ? element.getAttribute('{attr}') : '';
        }}
    """) or ""

async def extract_single_image_binary(scraper: WebScraper, selector: str) -> str:
    """Extract image as binary data (base64 encoded)"""
    try:
        logger.info(f"🖼️ Extracting image binary for selector: {selector}")
        
        # Try to get image directly from browser first (more efficient)
        binary_data = await get_image_from_browser(scraper, selector)
        
        if binary_data:
            return binary_data
        
        # Fallback: download from URL if browser extraction fails
        logger.info(f"🖼️ Browser extraction failed, trying URL download...")
        
        # First get the src attribute
        src_url = await scraper.page.evaluate(f"""
            () => {{
                const element = document.querySelector('{selector}');
                console.log('Found element:', element);
                if (!element) return null;
                
                // Try different src attributes
                const src = element.src || element.getAttribute('src') || element.getAttribute('data-src');
                console.log('Image src:', src);
                return src;
            }}
        """)
        
        logger.info(f"🖼️ Extracted src_url: {src_url}")
        
        if not src_url:
            logger.warning(f"⚠️ No image source found for selector: {selector}")
            return ""
        
        # Handle relative URLs
        if src_url.startswith('//'):
            src_url = 'https:' + src_url
        elif src_url.startswith('/'):
            # Get current page URL to construct absolute URL
            current_url = scraper.page.url
            base_url = '/'.join(current_url.split('/')[:3])
            src_url = base_url + src_url
        elif not src_url.startswith('http'):
            # Relative URL
            current_url = scraper.page.url
            base_url = '/'.join(current_url.split('/')[:-1])
            src_url = base_url + '/' + src_url
        
        logger.info(f"🖼️ Image URL: {src_url}")
        
        # Download and convert to base64
        binary_data = await download_image_binary(scraper, src_url)
        return binary_data or ""
        
    except Exception as e:
        logger.error(f"❌ Error extracting image binary for {selector}: {str(e)}")
        return ""

async def extract_collection_images_binary(scraper: WebScraper, selector: str) -> List[str]:
    """Extract multiple images as binary data (base64 encoded)"""
    try:
        # Get all image sources
        src_urls = await scraper.page.evaluate(f"""
            () => {{
                const elements = document.querySelectorAll('{selector}');
                const urls = [];
                
                for (let element of elements) {{
                    const src = element.src || element.getAttribute('src') || element.getAttribute('data-src');
                    if (src) urls.push(src);
                }}
                
                return urls;
            }}
        """)
        
        if not src_urls:
            logger.warning(f"⚠️ No image sources found for selector: {selector}")
            return []
        
        # Process each image URL
        binary_data_list = []
        for src_url in src_urls:
            # Handle relative URLs
            if src_url.startswith('//'):
                src_url = 'https:' + src_url
            elif src_url.startswith('/'):
                current_url = scraper.page.url
                base_url = '/'.join(current_url.split('/')[:3])
                src_url = base_url + src_url
            elif not src_url.startswith('http'):
                current_url = scraper.page.url
                base_url = '/'.join(current_url.split('/')[:-1])
                src_url = base_url + '/' + src_url
            
            logger.info(f"🖼️ Processing image URL: {src_url}")
            
            # Download and convert to base64
            binary_data = await download_image_binary(scraper, src_url)
            if binary_data:
                binary_data_list.append(binary_data)
            else:
                binary_data_list.append("")
        
        return binary_data_list
        
    except Exception as e:
        logger.error(f"❌ Error extracting images binary for {selector}: {str(e)}")
        return []

async def extract_collection_text(scraper: WebScraper, selector: str) -> List[str]:
    """Extract text from multiple elements"""
    texts = await scraper.page.evaluate(f"""
        () => {{
            const elements = document.querySelectorAll('{selector}');
            return Array.from(elements).map(el => 
                el.innerText || el.textContent || ''
            );
        }}
    """)
    # Clean up whitespace in Python
    return [clean_text(text) for text in texts if text.strip()]

async def extract_collection_html(scraper: WebScraper, selector: str) -> List[str]:
    """Extract HTML content from multiple elements"""
    return await scraper.page.evaluate(f"""
        () => {{
            const elements = document.querySelectorAll('{selector}');
            return Array.from(elements).map(el => el.outerHTML);
        }}
    """)

async def extract_collection_text_and_html(scraper: WebScraper, selector: str) -> List[Dict[str, str]]:
    """Extract both text and HTML from multiple elements"""
    results = await scraper.page.evaluate(f"""
        () => {{
            const elements = document.querySelectorAll('{selector}');
            return Array.from(elements).map(el => ({{
                text: el.innerText || el.textContent || '',
                html: el.outerHTML
            }}));
        }}
    """)
    # Clean up whitespace in Python
    cleaned_results = []
    for result in results:
        if result.get('text') or result.get('html'):
            result['text'] = clean_text(result['text'])
            cleaned_results.append(result)
    return cleaned_results

async def extract_collection_attributes(scraper: WebScraper, selector: str, attr: str) -> List[str]:
    """Extract attributes from multiple elements"""
    return await scraper.page.evaluate(f"""
        () => {{
            const elements = document.querySelectorAll('{selector}');
            return Array.from(elements).map(el => el.getAttribute('{attr}')).filter(val => val);
        }}
    """)

async def extract_collection_with_fields(scraper: WebScraper, selector: str, fields: Dict[str, Union[str, FieldSelector]], debug: bool = False) -> List[Dict[str, Any]]:
    """Extract collection with multiple fields"""
    # Parse fields to extract selectors and attributes
    field_configs = {}
    for field_name, field_value in fields.items():
        if isinstance(field_value, str):
            parsed_selector, attr = parse_selector_and_attr(field_value)
            field_configs[field_name] = {
                'selector': parsed_selector,
                'attr': attr
            }
        else:
            # FieldSelector object
            field_configs[field_name] = {
                'selector': field_value.selector,
                'attr': field_value.attr
            }
    
    # Debug: Log field configs
    logger.info(f"🔍 Field configs: {field_configs}")
    
    # Build JavaScript code for extraction
    debug_html_code = 'result["_debug_html"] = element.outerHTML;' if debug else ''
    
    js_code_parts = []
    for field_name, config in field_configs.items():
        field_selector = config['selector']
        attr = config['attr']
        
        if field_selector == "text":
            # Extract text from the element itself
            js_code_parts.append(f'''
                result["{field_name}"] = (element.innerText || element.textContent || "").trim();
            ''')
        elif field_selector.startswith("*"):
            # Wildcard navigation: * a(href) means find in any ancestor
            # Note: In 'collect', wildcard is usually unnecessary since fields are searched within each collection element
            # Wildcard is mainly useful for 'get' operations when navigating up the DOM tree
            actual_selector = field_selector.replace("*", "").strip()
            
            # Check if selector contains sibling operator (+)
            if '+' in actual_selector:
                # Handle sibling selector: .cell+.cell
                parts = actual_selector.split('+')
                if len(parts) == 2:
                    first_part = parts[0].strip()
                    second_part = parts[1].strip()
                    
                    if attr:
                        js_code_parts.append(f'''
                            let {field_name}_fieldElement = null;
                            let currentElement = element;
                            while (currentElement && !{field_name}_fieldElement) {{
                                const firstEl = currentElement.querySelector("{first_part}");
                                if (firstEl && firstEl.nextElementSibling) {{
                                    const sibling = firstEl.nextElementSibling;
                                    // Check if sibling matches second selector, if specified
                                    if ("{second_part}" && sibling.matches && sibling.matches("{second_part}")) {{
                                        {field_name}_fieldElement = sibling;
                                    }} else if ("{second_part}" === "") {{
                                        // If no second selector, just use next sibling
                                        {field_name}_fieldElement = sibling;
                                    }}
                                    if ({field_name}_fieldElement) break;
                                }}
                                currentElement = currentElement.parentElement;
                            }}
                            result["{field_name}"] = {field_name}_fieldElement ? 
                                ({field_name}_fieldElement.getAttribute("{attr}") || "") : "";
                        ''')
                    else:
                        js_code_parts.append(f'''
                            let {field_name}_fieldElement = null;
                            let currentElement = element;
                            while (currentElement && !{field_name}_fieldElement) {{
                                const firstEl = currentElement.querySelector("{first_part}");
                                if (firstEl && firstEl.nextElementSibling) {{
                                    const sibling = firstEl.nextElementSibling;
                                    // Check if sibling matches second selector, if specified
                                    if ("{second_part}" && sibling.matches && sibling.matches("{second_part}")) {{
                                        {field_name}_fieldElement = sibling;
                                    }} else if ("{second_part}" === "") {{
                                        // If no second selector, just use next sibling
                                        {field_name}_fieldElement = sibling;
                                    }}
                                    if ({field_name}_fieldElement) break;
                                }}
                                currentElement = currentElement.parentElement;
                            }}
                            result["{field_name}"] = {field_name}_fieldElement ? 
                                (({field_name}_fieldElement.innerText || {field_name}_fieldElement.textContent || "").trim()) : "";
                        ''')
                else:
                    # Fallback for invalid sibling syntax
                    js_code_parts.append(f'''
                        result["{field_name}"] = "";
                    ''')
            else:
                # Normal wildcard navigation without sibling
                # Search up the DOM tree starting from current element
                if attr:
                    js_code_parts.append(f'''
                        let {field_name}_fieldElement = null;
                        let currentElement = element;
                        while (currentElement && !{field_name}_fieldElement) {{
                            {field_name}_fieldElement = currentElement.querySelector("{actual_selector}");
                            if (!{field_name}_fieldElement) {{
                                currentElement = currentElement.parentElement;
                            }}
                        }}
                        result["{field_name}"] = {field_name}_fieldElement ? 
                            ({field_name}_fieldElement.getAttribute("{attr}") || "") : "";
                    ''')
                else:
                    js_code_parts.append(f'''
                        let {field_name}_fieldElement = null;
                        let currentElement = element;
                        while (currentElement && !{field_name}_fieldElement) {{
                            {field_name}_fieldElement = currentElement.querySelector("{actual_selector}");
                            if (!{field_name}_fieldElement) {{
                                currentElement = currentElement.parentElement;
                            }}
                        }}
                        result["{field_name}"] = {field_name}_fieldElement ? 
                            (({field_name}_fieldElement.innerText || {field_name}_fieldElement.textContent || "").trim()) : "";
                    ''')
        elif '<' in field_selector:
            # Handle parent navigation syntax like '.child<div<div>h1'
            parts = field_selector.split('<')
            if len(parts) >= 2:
                start_selector = parts[0].strip()
                remaining_parts = parts[1:]
                
                # Split the last part if it contains '>'
                if remaining_parts and '>' in remaining_parts[-1]:
                    last_part = remaining_parts[-1]
                    last_parts = last_part.split('>')
                    remaining_parts = remaining_parts[:-1] + last_parts
                
                target_selector = remaining_parts[-1].strip()
                parent_levels = len(remaining_parts) - 1
                
                js_code_parts.append(f'''
                    // Find starting element relative to current element
                    const startElement = element.querySelector("{start_selector}");
                    if (startElement) {{
                        // Go up {parent_levels} parent levels
                        let currentElement = startElement;
                        for (let i = 0; i < {parent_levels}; i++) {{
                            currentElement = currentElement.parentElement;
                            if (!currentElement) break;
                        }}
                        
                        // Find target element within the container
                        const targetElement = currentElement ? currentElement.querySelector("{target_selector}") : null;
                        result["{field_name}"] = targetElement ? 
                            (targetElement.innerText || targetElement.textContent || "").trim() : "";
                    }} else {{
                        result["{field_name}"] = "";
                    }}
                ''')
            else:
                # Fallback for invalid parent navigation syntax
                js_code_parts.append(f'''
                    result["{field_name}"] = "";
                ''')
        elif '+' in field_selector and not field_selector.startswith('*'):
            # Handle sibling selector without wildcard: .cell+.cell
            # In collect, all selectors are relative to the collection element, so no wildcard needed
            parts = field_selector.split('+')
            if len(parts) == 2:
                first_part = parts[0].strip()
                second_part = parts[1].strip()
                
                if attr:
                    js_code_parts.append(f'''
                        const {field_name}_firstEl = element.querySelector("{first_part}");
                        if ({field_name}_firstEl) {{
                            let sibling = {field_name}_firstEl.nextElementSibling;
                            // Find next sibling that matches the second selector
                            while (sibling && (!sibling.matches || !sibling.matches("{second_part}"))) {{
                                sibling = sibling.nextElementSibling;
                            }}
                            if (sibling) {{
                                result["{field_name}"] = sibling.getAttribute("{attr}") || "";
                            }} else {{
                                result["{field_name}"] = "";
                            }}
                        }} else {{
                            result["{field_name}"] = "";
                        }}
                    ''')
                else:
                    js_code_parts.append(f'''
                        const {field_name}_firstEl = element.querySelector("{first_part}");
                        if ({field_name}_firstEl) {{
                            let sibling = {field_name}_firstEl.nextElementSibling;
                            // Find next sibling that matches the second selector
                            while (sibling && (!sibling.matches || !sibling.matches("{second_part}"))) {{
                                sibling = sibling.nextElementSibling;
                            }}
                            if (sibling) {{
                                result["{field_name}"] = (sibling.innerText || sibling.textContent || "").trim();
                            }} else {{
                                result["{field_name}"] = "";
                            }}
                        }} else {{
                            result["{field_name}"] = "";
                        }}
                    ''')
            else:
                # Fallback for invalid sibling syntax
                js_code_parts.append(f'''
                    result["{field_name}"] = "";
                ''')
        elif attr:
            # Extract attribute
            if field_selector == "a" and attr == "href":
                # Special case for href attribute - get from the element itself
                js_code_parts.append(f'''
                    result["{field_name}"] = element.getAttribute("href") || "";
                ''')
            elif field_selector == "href":
                # Special case for href attribute - get from the element itself
                js_code_parts.append(f'''
                    result["{field_name}"] = element.getAttribute("href") || "";
                ''')
            else:
                js_code_parts.append(f'''
                    const {field_name}_fieldElement = element.querySelector("{field_selector}");
                    result["{field_name}"] = {field_name}_fieldElement ? 
                        {field_name}_fieldElement.getAttribute("{attr}") || "" : "";
                ''')
        else:
            # Extract text from child element
            if field_selector == "th":
                # Special handling for th elements with rowspan
                js_code_parts.append(f'''
                    const {field_name}_fieldElement = element.querySelector("{field_selector}");
                    if ({field_name}_fieldElement) {{
                        currentCategory = ({field_name}_fieldElement.innerText || {field_name}_fieldElement.textContent || "").trim();
                        result["{field_name}"] = currentCategory;
                    }} else {{
                        result["{field_name}"] = currentCategory;
                    }}
                ''')
            elif field_selector.lower() == "img":
                # Special case for img without attr - extract src URL for binary conversion
                js_code_parts.append(f'''
                    const {field_name}_fieldElement = element.querySelector("{field_selector}");
                    result["{field_name}_url"] = {field_name}_fieldElement ? 
                        ({field_name}_fieldElement.getAttribute("src") || "") : "";
                ''')
            else:
                js_code_parts.append(f'''
                    const {field_name}_fieldElement = element.querySelector("{field_selector}");
                    result["{field_name}"] = {field_name}_fieldElement ? 
                        ({field_name}_fieldElement.innerText || {field_name}_fieldElement.textContent || "").trim() : "";
                ''')
    
    js_code = '\n'.join(js_code_parts)
    
    # Debug: Log the JavaScript code
    logger.info(f"🔍 JavaScript code for collection: {js_code}")
    
    results = await scraper.page.evaluate(f"""
        () => {{
            const elements = document.querySelectorAll('{selector}');
            console.log('Found elements:', elements.length);
            console.log('Selector:', '{selector}');
            let currentCategory = '';
            const results = [];
            
            for (let i = 0; i < elements.length; i++) {{
                const element = elements[i];
                console.log('Processing element', i, element);
                const result = {{}};
                
                // Add HTML for debug if requested
                {debug_html_code}
                
                // Check if this row has a th element (category)
                const thElement = element.querySelector('th');
                if (thElement) {{
                    currentCategory = (thElement.innerText || thElement.textContent || '').trim();
                }}
                
                {js_code}
                console.log('Result for element', i, ':', result);
                results.push(result);
            }}
            
            console.log('Final results:', results);
            return results;
        }}
    """)
    
    logger.info(f"🔍 Collection results: {results}")
    
    # Clean up whitespace in Python and process image URLs
    cleaned_results = []
    for result in results:
        cleaned_result = {}
        for key, value in result.items():
            if isinstance(value, str):
                cleaned_result[key] = clean_text(value)
            else:
                cleaned_result[key] = value
        
        # Process image URLs and convert to binary data
        for key, value in result.items():
            if key.endswith('_url') and value:
                # This is an image URL that needs to be converted to binary
                field_name = key[:-4]  # Remove '_url' suffix
                
                # Handle relative URLs
                image_url = value
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url
                elif image_url.startswith('/'):
                    current_url = scraper.page.url
                    base_url = '/'.join(current_url.split('/')[:3])
                    image_url = base_url + image_url
                elif not image_url.startswith('http'):
                    current_url = scraper.page.url
                    base_url = '/'.join(current_url.split('/')[:-1])
                    image_url = base_url + '/' + image_url
                
                logger.info(f"🖼️ Converting image URL to binary: {image_url}")
                
                # Download and convert to base64
                binary_data = await download_image_binary(scraper, image_url)
                if binary_data:
                    cleaned_result[field_name] = binary_data
                else:
                    cleaned_result[field_name] = ""
                
                # Remove the temporary URL field
                if key in cleaned_result:
                    del cleaned_result[key]
        
        # Add all results without filtering
        cleaned_results.append(cleaned_result)
    
    return cleaned_results

@app.post("/scrape")
async def scrape_website(
    request: UnifiedScrapeRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Main scraping endpoint that supports multiple modes:
    
    1. **Simple HTML Source**: If no 'get' or 'collect' fields are provided, 
       returns the complete HTML source code of the page
       
    2. **Advanced Element Scraping**: If 'get' or 'collect' fields are provided,
       extracts specific elements using CSS selectors
       
    Parameters:
    - url: Target URL to scrape
    - use_proxy: Whether to use proxy (default: True)
    - proxy_url: Custom proxy URL (optional) - Supports HTTP, SOCKS4, SOCKS5
    - wait_time: Wait time in seconds (default: 3)
    - wait_for_element: Wait for specific element (default: False)
    - element_timeout: Timeout for element waiting (default: 30)
    - debug: Include debug HTML in response (default: False)
    - take_screenshot: Take screenshot (default: False)
    - extract_links: Extract all links from page (default: False)
    - get: Dictionary of single element extractions
    - collect: Dictionary of collection extractions
    
    Supported Proxy Types:
    - HTTP: http://proxy.com:8080
    - HTTPS: https://proxy.com:8080
    - SOCKS4: socks4://proxy.com:1080
    - SOCKS5: socks5://proxy.com:1080
    - With credentials: socks5://proxy.com:1080:username:password
    """
    
    # Check if this is a simple HTML request (no get/collect fields)
    if not request.get and not request.collect:
        # Simple HTML source code request
        logger.info("🎯 Simple HTML source request")
        return await scrape_html_source(request, api_key)
    else:
        # Unified scraping request
        logger.info("🎯 Using unified format")
        return await scrape_unified(request, api_key)

async def execute_clicks(scraper: WebScraper, click_selectors: List[str]):
    """
    Execute click operations in sequence with robust error handling
    
    Args:
        scraper: WebScraper instance
        click_selectors: List of CSS selectors to click in order
    
    Returns:
        True if all clicks succeeded, False otherwise
    """
    if not click_selectors or not scraper or not scraper.page:
        return True
    
    logger.info(f"🖱️ Executing {len(click_selectors)} click operations")
    
    for i, selector in enumerate(click_selectors, 1):
        try:
            logger.info(f"🖱️ [{i}/{len(click_selectors)}] Clicking element: {selector}")
            
            # Check if page is still valid
            try:
                if scraper.page.is_closed():
                    logger.error(f"❌ Page is closed, cannot execute clicks")
                    return False
            except:
                logger.error(f"❌ Page is no longer valid, cannot execute clicks")
                return False
            
            # Wait for element to be visible and clickable
            try:
                await scraper.page.wait_for_selector(selector, state='visible', timeout=10000)
                # Additional wait to ensure element is clickable
                await scraper.page.wait_for_selector(selector, state='attached', timeout=5000)
                logger.info(f"✅ Element found and ready: {selector}")
            except Exception as e:
                error_msg = str(e)
                # EPIPE and browser closed errors are critical
                if 'EPIPE' in error_msg or 'browser' in error_msg.lower() and 'closed' in error_msg.lower():
                    logger.error(f"❌ Browser connection lost: {error_msg}")
                    return False
                logger.warning(f"⚠️ Element not found or not visible: {selector} - {error_msg}")
                continue  # Skip this click if element not found
            
            # Store current URL to detect navigation
            try:
                current_url_before = scraper.page.url
            except Exception as e:
                error_msg = str(e)
                if 'EPIPE' in error_msg:
                    logger.error(f"❌ Browser connection lost during click: {error_msg}")
                    return False
                logger.warning(f"⚠️ Cannot get current URL: {error_msg}")
                continue
            
            # Click the element
            try:
                await scraper.page.click(selector, timeout=5000)
                logger.info(f"✅ Clicked: {selector}")
            except Exception as click_error:
                error_msg = str(click_error)
                if 'EPIPE' in error_msg or 'browser' in error_msg.lower() and 'closed' in error_msg.lower():
                    logger.error(f"❌ Browser connection lost during click: {error_msg}")
                    return False
                logger.error(f"❌ Failed to click {selector}: {error_msg}")
                continue
            
            # Minimum 100ms wait after click
            await asyncio.sleep(0.1)
            
            # Wait for page to stabilize after click
            try:
                current_url_after = scraper.page.url
                if current_url_before != current_url_after:
                    logger.info(f"🔄 URL changed: {current_url_before} -> {current_url_after}")
                    # Wait for new page to load
                    await scraper.page.wait_for_load_state('domcontentloaded', timeout=10000)
                    await scraper.page.wait_for_load_state('networkidle', timeout=10000)
                else:
                    # No navigation, but wait for any async DOM updates
                    await asyncio.sleep(0.2)  # Additional wait for async content
                    try:
                        await scraper.page.wait_for_load_state('networkidle', timeout=5000)
                    except:
                        # If networkidle times out, that's okay - continue anyway
                        pass
            except Exception as wait_error:
                error_msg = str(wait_error)
                if 'EPIPE' in error_msg:
                    logger.error(f"❌ Browser connection lost during wait: {error_msg}")
                    return False
                logger.warning(f"⚠️ Wait timeout after click: {error_msg}")
                # Continue anyway - page might still be usable
            
            logger.info(f"✅ Click {i}/{len(click_selectors)} completed successfully")
            
        except Exception as e:
            error_msg = str(e)
            if 'EPIPE' in error_msg:
                logger.error(f"❌ Browser connection lost: {error_msg}")
                return False
            logger.error(f"❌ Error executing click {i}/{len(click_selectors)} on {selector}: {error_msg}")
            # Continue with next click even if this one failed
            continue
    
    logger.info(f"✅ All click operations completed")
    return True

async def scrape_html_source(request: UnifiedScrapeRequest, api_key: str):
    """Simple HTML source code scraping endpoint"""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    screenshot_path = None
    links = None
    
    try:
        logger.info(f"📄 HTML source request {request_id}: {request.url}")
        
        # Get scraper instance
        scraper = await get_scraper()
        
        # Configure proxy
        if request.use_proxy:
            if request.proxy_url:
                logger.info(f"🔒 Using custom proxy: {request.proxy_url}")
            else:
                logger.info("🔒 Using proxy from configuration")
        
        # Navigate to URL
        logger.info(f"Navigating to: {request.url}")
        try:
            await scraper.navigate_to_url(str(request.url))
        except Exception as e:
            error_msg = f"Failed to navigate to URL: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            # Return scraper to pool on error
            try:
                await cleanup_scraper(scraper)
            except:
                pass
            
            return {
                "success": False,
                "url": str(request.url),
                "html_source": "",
                "content_length": 0,
                "load_time": time.time() - start_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": error_msg,
                "screenshot_path": None,
                "links": None,
                "proxy_used": scraper.get_current_proxy_info() if hasattr(scraper, 'get_current_proxy_info') else None
            }
        
        # Wait for element if specified
        if request.wait_for_element:
            logger.info(f"⏳ Waiting for element with timeout: {request.element_timeout}s")
            await asyncio.sleep(request.element_timeout)
        
        # Wait for page to load
        try:
            await scraper.page.wait_for_load_state('domcontentloaded', timeout=10000)
        except Exception as e:
            logger.warning(f"⚠️ DOM content loaded timeout: {str(e)}")
            # Check if page is accessible
            try:
                current_url = scraper.page.url
                if "about:blank" in current_url or not current_url:
                    error_msg = f"Page failed to load: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    
                    await cleanup_scraper(scraper)
                    return {
                        "success": False,
                        "url": str(request.url),
                        "html_source": "",
                        "content_length": 0,
                        "load_time": time.time() - start_time,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "error": error_msg,
                        "screenshot_path": None,
                        "links": None,
                        "proxy_used": scraper.get_current_proxy_info() if hasattr(scraper, 'get_current_proxy_info') else None
                    }
            except:
                pass
        
        if request.wait_time:
            logger.info(f"⏳ Waiting {request.wait_time} seconds")
            await asyncio.sleep(request.wait_time)

        # Wait for JavaScript to complete
        try:
            await scraper.page.wait_for_function("document.readyState === 'complete'", timeout=10000)
            await asyncio.sleep(1)
        except Exception as e:
            logger.warning(f"⚠️ DOM stabilization timeout: {str(e)}")

        logger.info("🪞 DOM ready for HTML extraction")

        # Execute click operations if specified
        if request.click:
            logger.info(f"🖱️ Click operations requested: {len(request.click)} clicks")
            await execute_clicks(scraper, request.click)
            # Wait a bit more after all clicks are done
            await asyncio.sleep(0.5)
            logger.info("✅ All click operations completed, proceeding with scraping")

        # Get HTML source code
        html_content = await scraper.page.content()
        
        # Get proxy information
        proxy_info = scraper.get_current_proxy_info()
        
        # Take screenshot if requested
        if request.take_screenshot:
            try:
                screenshot_path = await scraper.take_screenshot(request_id)
                logger.info(f"📸 Screenshot saved: {screenshot_path}")
            except Exception as e:
                logger.error(f"❌ Screenshot failed: {str(e)}")
        
        # Extract links if requested
        if request.extract_links:
            try:
                links = await scraper.extract_links()
                logger.info(f"🔗 Extracted {len(links)} links")
            except Exception as e:
                logger.error(f"❌ Link extraction failed: {str(e)}")
        
        # Get debug HTML if requested
        debug_html = ""
        if request.debug:
            debug_html = html_content
            logger.info(f"🔍 Debug HTML: {len(debug_html)} chars")
        
        # Return scraper to pool
        await cleanup_scraper(scraper)
        
        load_time = time.time() - start_time
        logger.info(f"✅ HTML source extraction completed {request_id}: {len(html_content)} chars in {load_time:.2f}s")
        
        response = {
            "success": True,
            "url": str(request.url),
            "html_source": html_content,
            "content_length": len(html_content),
            "load_time": load_time,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "screenshot_path": screenshot_path,
            "links": links,
            "proxy_used": proxy_info
        }
        
        # Add debug_html only if debug is enabled
        if request.debug and debug_html:
            response["debug_html"] = debug_html
            
        return response
        
    except Exception as e:
        load_time = time.time() - start_time
        error_msg = f"HTML source extraction failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        # Return scraper to pool on error - ensure cleanup even if scraper creation failed
        scraper_var = locals().get('scraper')
        if scraper_var:
            try:
                await cleanup_scraper(scraper_var)
            except Exception as cleanup_error:
                logger.error(f"❌ Cleanup failed in exception handler: {cleanup_error}")
        
        # Get proxy info even on error
        proxy_info = None
        if scraper_var:
            try:
                proxy_info = scraper_var.get_current_proxy_info()
            except:
                pass
        
        error_response = {
            "success": False,
            "url": str(request.url),
            "html_source": "",
            "content_length": 0,
            "load_time": load_time,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "error": error_msg,
            "screenshot_path": screenshot_path,
            "links": links,
            "proxy_used": proxy_info
        }
        
        # Add debug_html only if debug is enabled
        if request.debug and debug_html:
            error_response["debug_html"] = debug_html
            
        return error_response

async def scrape_unified(request: UnifiedScrapeRequest, api_key: str):
    """Unified scraping endpoint that supports both 'get' and 'collect' operations"""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    debug_html = ""
    screenshot_path = None
    links = None
    
    try:
        logger.info(f"🎯 Unified scraping request {request_id}: {request.url}")
        
        # Get scraper instance
        scraper = await get_scraper()
        
        # Configure proxy
        if request.use_proxy:
            if request.proxy_url:
                # Use custom proxy URL from request
                logger.info(f"🔒 Using custom proxy: {request.proxy_url}")
                # The proxy will be configured in the scraper setup
            else:
                logger.info("🔒 Using proxy from configuration")
        
        # Navigate to URL
        logger.info(f"Navigating to: {request.url}")
        try:
            await scraper.navigate_to_url(str(request.url))
        except Exception as e:
            error_msg = f"Failed to navigate to URL: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            # Return scraper to pool on error
            try:
                await cleanup_scraper(scraper)
            except:
                pass
            
            return {
                "success": False,
                "url": str(request.url),
                "data": {"get": {}, "collect": {}},
                "load_time": time.time() - start_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": error_msg,
                "screenshot_path": None,
                "links": None,
                "proxy_used": scraper.get_current_proxy_info() if hasattr(scraper, 'get_current_proxy_info') else None
            }
        
        # Wait for element if specified
        if request.wait_for_element:
            logger.info(f"⏳ Waiting for element with timeout: {request.element_timeout}s")
            # Note: wait_for_element method needs to be implemented in WebScraper
            await asyncio.sleep(request.element_timeout)
        
        # Wait for page to load and optional wait_time
        try:
            await scraper.page.wait_for_load_state('domcontentloaded', timeout=10000)
        except Exception as e:
            logger.warning(f"⚠️ DOM content loaded timeout: {str(e)}")
            # Check if page is accessible
            try:
                current_url = scraper.page.url
                if "about:blank" in current_url or not current_url:
                    error_msg = f"Page failed to load: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    
                    await cleanup_scraper(scraper)
                    return {
                        "success": False,
                        "url": str(request.url),
                        "data": {"get": {}, "collect": {}},
                        "load_time": time.time() - start_time,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "error": error_msg,
                        "screenshot_path": None,
                        "links": None,
                        "proxy_used": scraper.get_current_proxy_info() if hasattr(scraper, 'get_current_proxy_info') else None
                    }
            except:
                pass
        
        if request.wait_time:
            logger.info(f"⏳ Waiting {request.wait_time} seconds")
            await asyncio.sleep(request.wait_time)

        # JavaScript'in tam çalışmasını bekle ve sonra HTML'i al
        try:
            # DOM'un stabil olmasını bekle
            await scraper.page.wait_for_function("document.readyState === 'complete'", timeout=10000)
            # Ek olarak biraz daha bekle (JavaScript'in çalışması için)
            await asyncio.sleep(1)
        except Exception as e:
            logger.warning(f"⚠️ DOM stabilizasyonu bekleme hatası: {str(e)}")

        # DOM ready olduğunu log'la
        logger.info("🪞 DOM ready for scraping")

        # Execute click operations if specified
        if request.click:
            logger.info(f"🖱️ Click operations requested: {len(request.click)} clicks")
            await execute_clicks(scraper, request.click)
            # Wait a bit more after all clicks are done
            await asyncio.sleep(0.5)
            logger.info("✅ All click operations completed, proceeding with scraping")

        # Get proxy information
        proxy_info = scraper.get_current_proxy_info()

        # Initialize response data
        response_data = {
            "get": {},
            "collect": {}
        }
        
        # Process 'get' operations
        if request.get:
            logger.info(f"📥 Processing {len(request.get)} 'get' operations")
            for key, config in request.get.items():
                try:
                    # Support both string selector and dict config
                    if isinstance(config, str):
                        # String format: "selector" or "selector(attr)"
                        selector = config
                        value = await unified_parser(scraper, selector, operation_type="single")
                    else:
                        # Dict format: {"selector": "...", "attr": "..."}
                        selector = config["selector"]
                        attr = config.get("attr")
                        value = await unified_parser(scraper, selector, operation_type="single", attr=attr)
                    
                    response_data["get"][key] = value
                    logger.info(f"✅ Extracted '{key}': {len(str(value))} chars")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to extract '{key}': {str(e)}")
                    response_data["get"][key] = ""
        
        # Process 'collect' operations
        if request.collect:
            logger.info(f"📋 Processing {len(request.collect)} 'collect' operations")
            for key, config in request.collect.items():
                try:
                    selector = config["selector"]
                    fields = config.get("fields", {})
                    
                    # Use unified parser for collection extraction
                    items = await unified_parser(scraper, selector, operation_type="collection", fields=fields, debug=request.debug)
                    
                    response_data["collect"][key] = items
                    logger.info(f"✅ Extracted '{key}': {len(items)} items")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to extract '{key}': {str(e)}")
                    response_data["collect"][key] = []
        
        # Take screenshot if requested
        if request.take_screenshot:
            try:
                screenshot_path = await scraper.take_screenshot(request_id)
                logger.info(f"📸 Screenshot saved: {screenshot_path}")
            except Exception as e:
                logger.error(f"❌ Screenshot failed: {str(e)}")
        
        # Extract links if requested
        if request.extract_links:
            try:
                links = await scraper.extract_links()
                logger.info(f"🔗 Extracted {len(links)} links")
            except Exception as e:
                logger.error(f"❌ Link extraction failed: {str(e)}")
        
        # Get debug HTML if requested
        if request.debug:
            try:
                debug_html = await scraper.page.content()
                logger.info(f"🔍 Debug HTML: {len(debug_html)} chars")
            except Exception as e:
                logger.error(f"❌ Debug HTML failed: {str(e)}")
        
        # Return scraper to pool
        await cleanup_scraper(scraper)
        
        load_time = time.time() - start_time
        logger.info(f"✅ Unified scraping completed {request_id}: {len(str(response_data))} chars in {load_time:.2f}s")
        
        response = {
            "success": True,
            "url": str(request.url),
            "data": response_data,
            "load_time": load_time,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "screenshot_path": screenshot_path,
            "links": links,
            "proxy_used": proxy_info
        }
        
        # Add debug_html only if debug is enabled
        if request.debug and debug_html:
            response["debug_html"] = debug_html
            
        return response
        
    except Exception as e:
        load_time = time.time() - start_time
        error_msg = f"Unified scraping failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        # Return scraper to pool on error
        try:
            await cleanup_scraper(scraper)
        except:
            pass
        
        # Get proxy info even on error
        proxy_info = None
        scraper_var = locals().get('scraper')
        if scraper_var:
            try:
                proxy_info = scraper_var.get_current_proxy_info()
            except:
                pass
        
        error_response = {
            "success": False,
            "url": str(request.url),
            "data": {"get": {}, "collect": {}},
            "load_time": load_time,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "error": error_msg,
            "screenshot_path": screenshot_path,
            "links": links,
            "proxy_used": proxy_info
        }
        
        # Add debug_html only if debug is enabled
        if request.debug and debug_html:
            error_response["debug_html"] = debug_html
            
        return error_response

async def scrape_legacy(request: ScrapeRequest, api_key: str):
    """Legacy scraping endpoint for backward compatibility"""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    logger.info(f"📡 Legacy scraping request {request_id}: {request.url} (API Key: {api_key[:20]}...)")
    
    try:
        # Get scraper instance
        scraper = await get_scraper()
        
        # Configure proxy
        if request.use_proxy:
            if request.proxy_url:
                # Use custom proxy URL from request
                logger.info(f"🔒 Using custom proxy: {request.proxy_url}")
                # The proxy will be configured in the scraper setup
            else:
                logger.info("🔒 Using proxy from configuration")
        
        # Navigate to URL
        logger.info(f"Navigating to: {request.url}")
        try:
            await scraper.navigate_to_url(str(request.url))
        except Exception as e:
            error_msg = f"Failed to navigate to URL: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            # Return scraper to pool on error
            try:
                await cleanup_scraper(scraper)
            except:
                pass
            
            return {
                "success": False,
                "url": str(request.url),
                "status_code": 500,
                "content_length": 0,
                "html_content": "",
                "text_content": None,
                "links": None,
                "images": None,
                "screenshot_path": None,
                "proxy_used": None,
                "ip_address": None,
                "load_time": time.time() - start_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": error_msg
            }
        
        # Wait additional time
        if request.wait_time > 0:
            logger.info(f"⏳ Waiting {request.wait_time} seconds")
            await asyncio.sleep(request.wait_time)
        
        logger.info("Page loaded successfully")
        
        # Take screenshot if requested
        screenshot_path = None
        if request.take_screenshot:
            try:
                screenshot_path = await scraper.take_screenshot(request_id)
                logger.info(f"📸 Screenshot saved: {screenshot_path}")
            except Exception as e:
                logger.error(f"❌ Screenshot failed: {str(e)}")
        
        # Extract links if requested
        links = None
        if request.extract_links:
            try:
                links = await scraper.extract_links()
                logger.info(f"🔗 Extracted {len(links)} links")
            except Exception as e:
                logger.error(f"❌ Link extraction failed: {str(e)}")
        
        # Extract images if requested
        images = None
        if request.extract_images:
            try:
                images = await scraper.extract_images()
                logger.info(f"🖼️ Extracted {len(images)} images")
            except Exception as e:
                logger.error(f"❌ Image extraction failed: {str(e)}")
        
        # Get page content
        content = await scraper.page.content()
        
        # Extract text content if requested
        text_content = None
        if request.extract_text:
            try:
                text_content = await scraper.page.evaluate("() => document.body.innerText")
                logger.info(f"📝 Extracted {len(text_content)} chars of text")
            except Exception as e:
                logger.error(f"❌ Text extraction failed: {str(e)}")
        
        # Get proxy info
        proxy_used = scraper.get_next_proxy() if hasattr(scraper, 'get_next_proxy') else None
        
        # Get IP address
        ip_address = None
        try:
            await scraper.navigate_to_url("https://httpbin.org/ip")
            ip_response = await scraper.page.evaluate("() => document.body.innerText")
            ip_data = json.loads(ip_response)
            ip_address = ip_data.get("origin", "unknown")
            logger.info(f"🌐 IP Address: {ip_address}")
        except Exception as e:
            logger.error(f"❌ IP detection failed: {str(e)}")
        
        # Return to original URL
        await scraper.navigate_to_url(str(request.url))
        
        # Return scraper to pool
        await cleanup_scraper(scraper)
        
        load_time = time.time() - start_time
        logger.info(f"✅ Legacy scraping completed {request_id}: {len(content)} bytes in {load_time:.2f}s")
        
        return {
            "success": True,
            "url": str(request.url),
            "status_code": 200,
            "content_length": len(content),
            "html_content": content,
            "text_content": text_content,
            "links": links,
            "images": images,
            "screenshot_path": screenshot_path,
            "proxy_used": proxy_used,
            "ip_address": ip_address,
            "load_time": load_time,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        load_time = time.time() - start_time
        error_msg = f"Legacy scraping failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        # Return scraper to pool on error
        try:
            await cleanup_scraper(scraper)
        except:
            pass
        
        return {
            "success": False,
            "url": str(request.url),
            "status_code": 500,
            "content_length": 0,
            "html_content": "",
            "text_content": None,
            "links": None,
            "images": None,
            "screenshot_path": None,
            "proxy_used": None,
            "ip_address": None,
            "load_time": load_time,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "error": error_msg
        }

@app.post("/proxies")
async def get_available_proxies(api_key: str = Depends(verify_api_key)):
    """Get available proxy list"""
    return {
        "proxies": [
            "http://57.129.81.201:8080",
            "http://proxy1.example.com:8080",
            "http://proxy2.example.com:8080"
        ],
        "default": "http://57.129.81.201:8080"
    }

@app.post("/test-proxy")
async def test_proxy(
    proxy_url: str,
    api_key: str = Depends(verify_api_key)
):
    """Test proxy connection"""
    scraper = None
    try:
        scraper = await get_scraper()
        # Test with specific proxy URL
        test_proxy_list = [{"url": proxy_url, "country": "Test", "type": "HTTP", "status": "working", "speed": "unknown", "last_tested": "2025-01-09"}]
        scraper.proxy_list = test_proxy_list
        scraper.current_proxy_index = 0
        
        try:
            await scraper.navigate_to_url("https://httpbin.org/ip")
        except Exception as e:
            await cleanup_scraper(scraper)
            return {
                "proxy": proxy_url,
                "working": False,
                "error": f"Failed to navigate with proxy: {str(e)}"
            }
        
        try:
            ip_response = await scraper.page.evaluate("() => document.body.innerText")
            ip_data = json.loads(ip_response)
        except Exception as e:
            await cleanup_scraper(scraper)
            return {
                "proxy": proxy_url,
                "working": False,
                "error": f"Failed to get IP response: {str(e)}"
            }
        
        await cleanup_scraper(scraper)
        
        return {
            "proxy": proxy_url,
            "working": True,
            "ip": ip_data.get("origin", "unknown")
        }
        
    except Exception as e:
        if scraper:
            try:
                await cleanup_scraper(scraper)
            except:
                pass
        
        return {
            "proxy": proxy_url,
            "working": False,
            "error": f"Proxy test failed: {str(e)}"
        }

# Duplicate function removed - using unified_parser instead

if __name__ == "__main__":
    import uvicorn
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get host and port from environment variables with defaults
    api_host = os.getenv('API_HOST', '127.0.0.1')
    api_port = int(os.getenv('API_PORT', '8888'))
    
    # If host is 127.0.0.1, change to 0.0.0.0 for external access
    if api_host == '127.0.0.1':
        api_host = '0.0.0.0'
        logger.info("🌐 Host changed from 127.0.0.1 to 0.0.0.0 for external access")
    
    # SSL/HTTPS Configuration
    ssl_enabled = os.getenv('SSL_ENABLED', 'false').lower() == 'true'
    ssl_keyfile = os.getenv('SSL_KEY_FILE', './ssl/key.pem')
    ssl_certfile = os.getenv('SSL_CERT_FILE', './ssl/cert.pem')
    
    if ssl_enabled:
        # Check if SSL files exist
        if os.path.exists(ssl_keyfile) and os.path.exists(ssl_certfile):
            logger.info(f"🔒 HTTPS enabled - Starting secure server on https://{api_host}:{api_port}")
            logger.info(f"🔑 Using SSL certificate: {ssl_certfile}")
            logger.info(f"🔐 Using SSL key: {ssl_keyfile}")
            uvicorn.run(
                app, 
                host=api_host, 
                port=api_port,
                ssl_keyfile=ssl_keyfile,
                ssl_certfile=ssl_certfile
            )
        else:
            logger.error("❌ SSL files not found! Please run install.sh to generate SSL certificates.")
            logger.error(f"   Missing: {ssl_keyfile if not os.path.exists(ssl_keyfile) else ssl_certfile}")
            logger.info("🔓 Falling back to HTTP mode")
            logger.info(f"🚀 Starting server on http://{api_host}:{api_port}")
            uvicorn.run(app, host=api_host, port=api_port)
    else:
        logger.info(f"🔓 HTTPS disabled - Starting HTTP server on http://{api_host}:{api_port}")
        logger.info("   To enable HTTPS, set SSL_ENABLED=true in .env file")
        uvicorn.run(app, host=api_host, port=api_port) 