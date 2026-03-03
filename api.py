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
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.responses import JSONResponse, FileResponse
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
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

VALID_API_KEYS = os.getenv('VALID_API_KEYS', 'sk-demo-key-12345').split(',')

# Debug screenshots: folder and retention
DEBUG_DIR = "debug"
DEBUG_MAX_AGE_DAYS = 5

# Domain sessions: keep per-domain storage_state + sticky proxy for 1 day
SESSION_TTL_SECONDS = 24 * 60 * 60  # 1 day
domain_sessions: Dict[str, Dict[str, Any]] = {}


def _ensure_debug_dir() -> str:
    os.makedirs(DEBUG_DIR, exist_ok=True)
    return DEBUG_DIR


def _cleanup_old_debug_files() -> None:
    """Remove debug files older than DEBUG_MAX_AGE_DAYS to avoid accumulation."""
    try:
        _ensure_debug_dir()
        now = time.time()
        max_age_seconds = DEBUG_MAX_AGE_DAYS * 24 * 3600
        for name in os.listdir(DEBUG_DIR):
            if name == ".gitkeep":
                continue
            path = os.path.join(DEBUG_DIR, name)
            if not os.path.isfile(path):
                continue
            if now - os.path.getmtime(path) > max_age_seconds:
                try:
                    os.remove(path)
                    logger.info(f"🗑️ Removed old debug file: {path}")
                except OSError as e:
                    logger.warning(f"Could not remove old debug file {path}: {e}")
    except OSError as e:
        logger.warning(f"Debug cleanup error: {e}")


def _get_domain_from_url(url: str) -> Optional[str]:
    """Extract hostname (domain) from URL string."""
    try:
        parsed = urlparse(str(url))
        return parsed.hostname
    except Exception:
        return None


def _get_valid_domain_session(domain: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return cached session for domain if it exists and is not expired."""
    if not domain:
        return None

    session = domain_sessions.get(domain)
    if not session:
        return None

    created_at = session.get("created_at")
    if not isinstance(created_at, (int, float)):
        return None

    if time.time() - created_at > SESSION_TTL_SECONDS:
        # Session expired, remove it
        domain_sessions.pop(domain, None)
        logger.info(f"🗑️ Domain session expired for {domain}")
        return None

    return session


async def _store_domain_session(scraper: WebScraper, url: str) -> None:
    """Store storage_state + proxy index for a domain after successful load."""
    domain = _get_domain_from_url(url)
    if not domain:
        return

    try:
        storage_state = None
        if getattr(scraper, "context", None) is not None:
            storage_state = await scraper.context.storage_state()

        proxy_index = getattr(scraper, "current_proxy_index", None)
        domain_sessions[domain] = {
            "created_at": time.time(),
            "proxy_index": proxy_index,
            "storage_state": storage_state,
        }
        logger.info(f"💾 Stored domain session for {domain} (proxy_index={proxy_index})")
    except Exception as e:
        logger.warning(f"⚠️ Failed to store domain session for {domain}: {e}")


async def _test_proxy_connectivity(scraper: WebScraper) -> Dict[str, Any]:
    """
    Test current proxy by hitting a fast external endpoint.
    Returns a small dict with success flag, ip (if any), and error message.
    """
    test_url = "https://httpbin.org/ip"
    result: Dict[str, Any] = {
        "success": False,
        "ip": None,
        "error": None,
        "test_url": test_url,
    }

    if not scraper or not getattr(scraper, "page", None):
        result["error"] = "No active page to run proxy test"
        return result

    try:
        await scraper.page.goto(test_url, wait_until="domcontentloaded", timeout=8000)
        try:
            body = await scraper.page.evaluate("() => document.body.innerText")
            ip_data = json.loads(body)
            result["ip"] = ip_data.get("origin")
            result["success"] = True
        except Exception as parse_err:
            result["error"] = f"IP parse failed: {parse_err}"
    except Exception as e:
        result["error"] = str(e)

    return result


async def _save_debug_html(scraper: WebScraper, html_path: str) -> Optional[str]:
    """Save current page HTML to html_path (e.g. debug/abc123_00_initial.html). Same base name as screenshot."""
    if not scraper or not scraper.page:
        return None
    try:
        html = await scraper.page.content()
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"📄 Debug HTML: {html_path}")
        return html_path
    except Exception as e:
        logger.error(f"Debug HTML save failed: {e}")
        return None


async def _save_debug_screenshot(scraper: WebScraper, filepath: str) -> Optional[str]:
    """Save a screenshot to filepath (e.g. debug/abc123_00_initial.png). Also saves same-name .html. Ensures dir exists and prunes old files."""
    if not scraper or not scraper.page:
        return None
    _ensure_debug_dir()
    _cleanup_old_debug_files()
    try:
        await scraper.take_screenshot(filepath)
        logger.info(f"📸 Debug screenshot: {filepath}")
        # Overlay coordinate grid on the screenshot to help with x/y based clicks
        try:
            from PIL import Image, ImageDraw, ImageFont

            img = Image.open(filepath).convert("RGB")
            draw = ImageDraw.Draw(img)
            width, height = img.size

            # Try a slightly bigger font; fallback to default
            try:
                font = ImageFont.truetype("arial.ttf", 14)
            except Exception:
                font = ImageFont.load_default()

            step = 100  # grid size in pixels
            # Very light grid, darker text for readability
            line_color = (210, 210, 210)  # light gray
            text_color = (60, 60, 60)     # dark gray

            # Draw grid lines
            for x in range(0, width, step):
                draw.line([(x, 0), (x, height)], fill=line_color, width=1)
            for y in range(0, height, step):
                draw.line([(0, y), (width, y)], fill=line_color, width=1)

            # Draw coordinate labels at intersections (every 200px to avoid clutter)
            for x in range(0, width, step):
                for y in range(0, height, step):
                    if x % 200 == 0 and y % 200 == 0:
                        label = f"{x}x{y}"
                        draw.text((x + 4, y + 4), label, font=font, fill=text_color)

            # If we have a last coordinate click marker and this is an after-click screenshot,
            # draw a visible crosshair at that position
            marker = getattr(scraper, "_last_click_coords", None)
            if marker and "_after_click_" in os.path.basename(filepath):
                mx, my = marker
                cross_color = (255, 0, 0)  # red for visibility
                size = 8
                # Horizontal line
                draw.line([(mx - size, my), (mx + size, my)], fill=cross_color, width=2)
                # Vertical line
                draw.line([(mx, my - size), (mx, my + size)], fill=cross_color, width=2)
                # Small label near marker
                draw.text((mx + 6, my + 6), f"{mx}x{my}", font=font, fill=cross_color)

            img.save(filepath)
            logger.info("🧭 Debug grid overlay applied to screenshot")
        except ImportError:
            # Pillow is optional at runtime; if missing, just keep raw screenshot
            logger.warning("Pillow not installed, skipping debug grid overlay")
        except Exception as grid_err:
            logger.warning(f"⚠️ Failed to apply debug grid overlay: {grid_err}")

        # Save page HTML with same base name, .html extension
        html_path = filepath.rsplit(".", 1)[0] + ".html" if "." in filepath else filepath + ".html"
        await _save_debug_html(scraper, html_path)
        return filepath
    except Exception as e:
        logger.error(f"Debug screenshot failed: {e}")
        return None

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
    # CSS selectors (strings) and/or waits (integers, milliseconds) in sequence.
    # Use "__verify_human__" to click "Verify you are human" on challenge pages.
    click: Optional[List[Union[str, int]]] = None
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
    debug_files: Optional[List[str]] = None

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

# Scraper pool (currently unused, kept for compatibility)
scraper_pool = []


async def get_scraper(domain: Optional[str] = None):
    """Get scraper instance with optional per-domain session and sticky proxy."""
    import random

    scraper = None
    try:
        # Create new scraper
        scraper = WebScraper()

        # Try to reuse existing domain session (storage_state + proxy index)
        session = _get_valid_domain_session(domain) if domain else None

        if session and scraper.proxy_list:
            proxy_index = session.get("proxy_index")
            if isinstance(proxy_index, int) and 0 <= proxy_index < len(scraper.proxy_list):
                scraper.current_proxy_index = proxy_index
                logger.info(f"🎯 Reusing session proxy index {proxy_index} for domain {domain}")
            elif scraper.proxy_list:
                scraper.current_proxy_index = random.randint(0, len(scraper.proxy_list) - 1)
                logger.info(f"🎲 Random proxy selected: index {scraper.current_proxy_index}")
        else:
            # No existing session, keep current behaviour: random proxy rotation
            if scraper.proxy_list:
                scraper.current_proxy_index = random.randint(0, len(scraper.proxy_list) - 1)
                logger.info(f"🎲 Random proxy selected: index {scraper.current_proxy_index}")

        storage_state = session.get("storage_state") if session else None

        await scraper.setup_browser(storage_state=storage_state)
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


@app.get("/scrape")
async def scrape_usage():
    """Return usage hint when GET is used instead of POST."""
    return JSONResponse(
        status_code=200,
        content={
            "message": "Use POST with JSON body. Example: curl -X POST http://127.0.0.1:8888/scrape -H 'Content-Type: application/json' -H 'X-API-Key: sk-demo-key-12345' -d '{\"url\":\"https://example.com\",\"use_proxy\":false,\"wait_time\":2}'",
            "required": {"url": "string"},
            "required_header": "X-API-Key",
        },
    )


@app.post("/scrape")
async def scrape_website(
    request: UnifiedScrapeRequest,
    api_key: str = Depends(verify_api_key),
    http_request: Request = None,
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
    try:
        # Check if this is a simple HTML request (no get/collect fields)
        if not request.get and not request.collect:
            # Simple HTML source code request
            logger.info("🎯 Simple HTML source request")
            return await scrape_html_source(request, api_key, http_request)
        else:
            # Unified scraping request
            logger.info("🎯 Using unified format")
            return await scrape_unified(request, api_key, http_request)
    except Exception as e:
        logger.exception("❌ Scrape endpoint error")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "message": "Scraping failed. Check server logs for details.",
            },
        )


# Special click target: "Verify you are human" checkbox on challenge pages (runs inside iframe)
VERIFY_HUMAN_SELECTOR = "__verify_human__"


async def _is_challenge_page(scraper: WebScraper) -> bool:
    """True if the current page is a security verification / challenge page."""
    try:
        if not scraper or not scraper.page or scraper.page.is_closed():
            return False
        title = (await scraper.page.title()).lower()
        if "just a moment" in title:
            return True
        body = await scraper.page.content()
        return "Performing security verification" in body or "cf-turnstile" in body
    except Exception:
        return False


async def _click_verify_human(scraper: WebScraper) -> bool:
    """Find challenge iframe and click the verify-human widget. Returns True if clicked."""
    try:
        page = scraper.page
        if not page or page.is_closed():
            return False
        await asyncio.sleep(3)
        iframe_selectors = [
            "iframe[src*='turnstile']",
            "iframe[src*='challenges']",
            "iframe[title*='Widget containing']",
        ]
        for iframe_sel in iframe_selectors:
            try:
                frame = page.frame_locator(iframe_sel).first
                for inner in [
                    "input[type='checkbox']",
                    "[role='checkbox']",
                    "label:has-text('Verify')",
                    "label:has-text('human')",
                    ".mark",
                    "#cf-turnstile",
                ]:
                    try:
                        loc = frame.locator(inner).first
                        await loc.wait_for(state="visible", timeout=3000)
                        await loc.click(timeout=5000)
                        logger.info("✅ Verify-human checkbox clicked")
                        return True
                    except Exception:
                        continue
            except Exception:
                continue
        logger.warning("⚠️ Verify-human iframe/checkbox not found")
        return False
    except Exception as e:
        logger.warning(f"⚠️ Verify-human click failed: {e}")
        return False


async def execute_clicks(
    scraper: WebScraper,
    click_selectors: List[Union[str, int]],
    request_id: Optional[str] = None,
    errors: Optional[List[str]] = None,
):
    """
    Execute click operations in sequence with robust error handling.
    When request_id is set, saves a debug screenshot after each click.
    Special selector "__verify_human__": clicks "Verify you are human" inside challenge iframe.
    Syntax "iframe:IFRAME_SEL >> INNER_SEL": click INNER_SEL inside the given iframe.

    Args:
        scraper: WebScraper instance
        click_selectors: List of CSS selectors (or special/iframe syntax) to click in order,
            and/or integers treated as waits in milliseconds
        request_id: Optional id for debug screenshots (e.g. after each click)
        errors: Optional list to append warning/error messages for API response

    Returns:
        True if all clicks succeeded, False otherwise
    """
    if not click_selectors or not scraper or not scraper.page:
        return True

    total_steps = len(click_selectors)
    total_clicks = sum(1 for item in click_selectors if not isinstance(item, (int, float)))
    if total_clicks > 0:
        logger.info(f"🖱️ Executing {total_clicks} click operations with {total_steps - total_clicks} wait steps")
    else:
        logger.info(f"🕒 Executing {total_steps} wait steps (no clickable selectors)")

    click_index = 0

    for step_index, item in enumerate(click_selectors, 1):
        # Integer/number entries are treated as waits in milliseconds between clicks
        if isinstance(item, (int, float)):
            wait_ms = max(int(item), 0)
            if wait_ms > 0:
                logger.info(f"⏳ [step {step_index}/{total_steps}] Waiting {wait_ms} ms before next click")
                try:
                    await asyncio.sleep(wait_ms / 1000.0)
                except Exception as e:
                    error_msg = str(e)
                    if 'EPIPE' in error_msg:
                        logger.error(f"❌ Browser connection lost during wait step: {error_msg}")
                        return False
                    msg = f"Error during wait step {step_index}: {error_msg}"
                    logger.warning(f"⚠️ {msg}")
                    if errors is not None:
                        errors.append(msg)
            else:
                logger.info(f"⏳ [step {step_index}/{total_steps}] Skipping non-positive wait value: {item}")
            continue

        selector = item

        try:
            click_index += 1
            logger.info(f"🖱️ [click {click_index}/{total_clicks}] Clicking element: {selector}")

            # Check if page is still valid
            try:
                if scraper.page.is_closed():
                    logger.error("❌ Page is closed, cannot execute clicks")
                    return False
            except Exception:
                logger.error("❌ Page is no longer valid, cannot execute clicks")
                return False

            # Reset last coordinate marker by default (only coordinate clicks will set it)
            try:
                setattr(scraper, "_last_click_coords", None)
            except Exception:
                pass

            # Normalize selector and detect click mode
            raw_selector = selector.strip()
            physical_only = False
            if raw_selector.startswith("physical:"):
                physical_only = True
                raw_selector = raw_selector[len("physical:") :].strip()

            # Coordinate click syntax: "100x200" -> click at (100, 200)
            coord_match = None
            try:
                # Match two integers separated by 'x' or 'X', optional spaces
                coord_match = re.fullmatch(r"(\d+)\s*[xX]\s*(\d+)", raw_selector)
            except Exception:
                coord_match = None

            if coord_match:
                try:
                    x = int(coord_match.group(1))
                    y = int(coord_match.group(2))
                    try:
                        setattr(scraper, "_last_click_coords", (x, y))
                    except Exception:
                        pass
                    current_url_before = scraper.page.url
                    # Move mouse to coordinate first (more "human-like"), then click
                    try:
                        await scraper.page.mouse.move(x, y, steps=10)
                    except Exception:
                        # If move fails, still attempt direct click
                        pass
                    await scraper.page.mouse.click(x, y)
                    clicked = True
                    logger.info(f"✅ Coordinate click at ({x}, {y})")
                except Exception as e:
                    error_msg = str(e)
                    if 'EPIPE' in error_msg or ('browser' in error_msg.lower() and 'closed' in error_msg.lower()):
                        logger.error(f"❌ Browser connection lost during coordinate click: {error_msg}")
                        return False
                    msg = f"Coordinate click failed at ({raw_selector}): {error_msg}"
                    logger.error(f"❌ {msg}")
                    if errors is not None:
                        errors.append(msg)
                    continue

            # Special: verify-human checkbox (inside challenge iframe)
            elif raw_selector == VERIFY_HUMAN_SELECTOR:
                current_url_before = scraper.page.url
                clicked = await _click_verify_human(scraper)
                if clicked:
                    await asyncio.sleep(2.0)  # allow challenge to complete
                else:
                    continue
            # Syntax: iframe:IFRAME_SEL >> INNER_SEL — click inside iframe
            elif raw_selector.startswith("iframe:") and " >> " in raw_selector:
                parts = raw_selector.replace("iframe:", "", 1).split(" >> ", 1)
                if len(parts) != 2:
                    msg = f"Invalid iframe selector: {selector}"
                    logger.warning(f"⚠️ {msg}")
                    if errors is not None:
                        errors.append(msg)
                    continue
                iframe_sel, inner_sel = parts[0].strip(), parts[1].strip()
                try:
                    frame = scraper.page.frame_locator(iframe_sel).first
                    await frame.locator(inner_sel).first.wait_for(state="visible", timeout=10000)
                    await frame.locator(inner_sel).first.click(timeout=5000)
                    clicked = True
                    logger.info(f"✅ Clicked inside iframe: {inner_sel}")
                except Exception as e:
                    msg = f"Iframe click failed: {e}"
                    logger.error(f"❌ {msg}")
                    if errors is not None:
                        errors.append(msg)
                    continue
                current_url_before = scraper.page.url
            else:
                # Normal main-frame selector
                try:
                    await scraper.page.wait_for_selector(raw_selector, state='visible', timeout=10000)
                    await scraper.page.wait_for_selector(raw_selector, state='attached', timeout=5000)
                    logger.info(f"✅ Element found and ready: {raw_selector}")
                except Exception as e:
                    error_msg = str(e)
                    if 'EPIPE' in error_msg or ('browser' in error_msg.lower() and 'closed' in error_msg.lower()):
                        logger.error(f"❌ Browser connection lost: {error_msg}")
                        return False
                    msg = f"Element not found or not visible: {selector} - {error_msg}"
                    logger.warning(f"⚠️ {msg}")
                    if errors is not None:
                        errors.append(msg)
                    continue

                try:
                    current_url_before = scraper.page.url
                except Exception as e:
                    error_msg = str(e)
                    if 'EPIPE' in error_msg:
                        logger.error(f"❌ Browser connection lost during click: {error_msg}")
                        return False
                    msg = f"Cannot get current URL: {error_msg}"
                    logger.warning(f"⚠️ {msg}")
                    if errors is not None:
                        errors.append(msg)
                    continue

                clicked = False
                try:
                    await scraper.page.click(raw_selector, timeout=5000)
                    clicked = True
                    logger.info(f"✅ Clicked: {raw_selector}")
                except Exception as click_error:
                    error_msg = str(click_error)
                    if 'EPIPE' in error_msg or ('browser' in error_msg.lower() and 'closed' in error_msg.lower()):
                        logger.error(f"❌ Browser connection lost during click: {error_msg}")
                        return False
                    # Optional JS fallback (skipped when physical_only=True)
                    if not physical_only:
                        try:
                            did_click = await scraper.page.evaluate(
                                """(sel) => { const el = document.querySelector(sel); if (el) { el.click(); return true; } return false; }""",
                                raw_selector,
                            )
                            if did_click:
                                clicked = True
                                logger.info(f"✅ Clicked via JavaScript (overlay bypass): {raw_selector}")
                        except Exception as js_click_err:
                            msg = f"JS click fallback failed for {raw_selector}: {js_click_err}"
                            logger.error(f"❌ {msg}")
                            if errors is not None:
                                errors.append(msg)
                    if not clicked:
                        msg = f"Failed to click {raw_selector}: {error_msg}"
                        logger.error(f"❌ {msg}")
                        if errors is not None:
                            errors.append(msg)
                        continue
            
            # Brief wait so DOM/JS updates (e.g. revealed content) after click are applied
            await asyncio.sleep(0.3)
            
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
                msg = f"Wait timeout after click: {error_msg}"
                logger.warning(f"⚠️ {msg}")
                if errors is not None:
                    errors.append(msg)
                # Continue anyway - page might still be usable

            logger.info(f"✅ Click {click_index}/{total_clicks} completed successfully")

            # Debug: save screenshot after this click when request_id is provided
            if request_id and clicked:
                try:
                    await _save_debug_screenshot(
                        scraper,
                        os.path.join(DEBUG_DIR, f"{request_id}_01_after_click_{click_index}.png"),
                    )
                except Exception:
                    pass

        except Exception as e:
            error_msg = str(e)
            if 'EPIPE' in error_msg:
                logger.error(f"❌ Browser connection lost: {error_msg}")
                return False
            msg = f"Error executing click step {step_index}/{total_steps} on {selector}: {error_msg}"
            logger.error(f"❌ {msg}")
            if errors is not None:
                errors.append(msg)
            # Continue with next click even if this one failed
            continue
    
    logger.info(f"✅ All click operations completed")
    return True

async def scrape_html_source(request: UnifiedScrapeRequest, api_key: str, http_request: Request):
    """Simple HTML source code scraping endpoint"""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    screenshot_path = None
    links = None
    errors: List[str] = []
    debug_files: List[str] = []

    try:
        logger.info(f"📄 HTML source request {request_id}: {request.url}")

        # Get scraper instance (per-domain session + sticky proxy when available)
        domain = _get_domain_from_url(str(request.url))
        scraper = await get_scraper(domain=domain)
        
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

            # On navigation failure: test proxy, mark it as failed, and drop domain session
            proxy_test = None
            try:
                if request.use_proxy:
                    proxy_test = await _test_proxy_connectivity(scraper)
            except Exception as proxy_err:
                logger.error(f"❌ Proxy test failed: {proxy_err}")

            try:
                proxy_info = scraper.get_current_proxy_info()
                if proxy_info and "url" in proxy_info:
                    scraper.mark_proxy_failed(proxy_info["url"])
            except Exception as mark_err:
                logger.warning(f"⚠️ Could not mark proxy as failed: {mark_err}")

            try:
                domain = _get_domain_from_url(str(request.url))
                if domain and domain in domain_sessions:
                    domain_sessions.pop(domain, None)
                    logger.info(f"🗑️ Dropped domain session for {domain} due to navigation failure")
            except Exception:
                pass

            try:
                await cleanup_scraper(scraper)
            except Exception:
                pass
            return {
                "success": False,
                "url": str(request.url),
                "error": error_msg,
                "load_time": time.time() - start_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "proxy_used": scraper.get_current_proxy_info() if hasattr(scraper, 'get_current_proxy_info') else None,
                "proxy_test": proxy_test,
            }

        # Wait for element if specified
        if request.wait_for_element:
            logger.info(f"⏳ Waiting for element with timeout: {request.element_timeout}s")
            await asyncio.sleep(request.element_timeout)

        # Wait for page to load
        try:
            await scraper.page.wait_for_load_state('domcontentloaded', timeout=10000)
        except Exception as e:
            msg = f"DOM content loaded timeout: {str(e)}"
            logger.warning(f"⚠️ {msg}")
            errors.append(msg)
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
                        "error": error_msg,
                        "load_time": time.time() - start_time,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "proxy_used": scraper.get_current_proxy_info() if hasattr(scraper, 'get_current_proxy_info') else None,
                    }
            except Exception:
                pass

        if request.wait_time:
            logger.info(f"⏳ Waiting {request.wait_time} seconds")
            await asyncio.sleep(request.wait_time)

        # Wait for JavaScript to complete
        try:
            await scraper.page.wait_for_function("document.readyState === 'complete'", timeout=10000)
            await asyncio.sleep(1)
        except Exception as e:
            msg = f"DOM stabilization timeout: {str(e)}"
            logger.warning(f"⚠️ {msg}")
            errors.append(msg)

        logger.info("🪞 DOM ready for HTML extraction")

        # Debug: save initial page screenshot (only when debug=true)
        if request.debug:
            first_path = await _save_debug_screenshot(
                scraper,
                os.path.join(DEBUG_DIR, f"{request_id}_00_initial.png"),
            )
            if first_path:
                debug_files.append(first_path)

        # Execute click operations if specified
        if request.click:
            logger.info(f"🖱️ Click operations requested: {len(request.click)} clicks")
            await execute_clicks(
                scraper,
                request.click,
                request_id=request_id if request.debug else None,
                errors=errors,
            )
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
                msg = f"Screenshot failed: {str(e)}"
                logger.error(f"❌ {msg}")
                errors.append(msg)

        # Extract links if requested
        if request.extract_links:
            try:
                links = await scraper.extract_links()
                logger.info(f"🔗 Extracted {len(links)} links")
            except Exception as e:
                msg = f"Link extraction failed: {str(e)}"
                logger.error(f"❌ {msg}")
                errors.append(msg)
        
        # Get debug HTML and file list if requested
        debug_html = ""
        if request.debug:
            debug_html = html_content
            logger.info(f"🔍 Debug HTML: {len(debug_html)} chars")
            # Collect all debug files for this request id (screenshots + HTML)
            try:
                _ensure_debug_dir()
                base_url = str(http_request.base_url).rstrip("/") if http_request else ""
                prefix = f"{request_id}_"
                debug_files = sorted(
                    (
                        f"{base_url}/debug/{name}?api_key={api_key}"
                        if base_url
                        else f"/debug/{name}?api_key={api_key}"
                    )
                    for name in os.listdir(DEBUG_DIR)
                    if name.startswith(prefix)
                )
            except Exception:
                debug_files = debug_files or []
        
        # Store domain session on successful page load
        await _store_domain_session(scraper, str(request.url))

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
            "proxy_used": proxy_info,
            "errors": errors,
        }
        if request.debug:
            if debug_html:
                response["debug_html"] = debug_html
            response["debug_files"] = debug_files
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
        
        return {
            "success": False,
            "url": str(request.url),
            "error": error_msg,
            "load_time": load_time,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "proxy_used": proxy_info,
        }

async def scrape_unified(request: UnifiedScrapeRequest, api_key: str, http_request: Request):
    """Unified scraping endpoint that supports both 'get' and 'collect' operations"""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    debug_html = ""
    screenshot_path = None
    links = None
    errors: List[str] = []
    debug_files: List[str] = []

    try:
        logger.info(f"🎯 Unified scraping request {request_id}: {request.url}")

        # Get scraper instance (per-domain session + sticky proxy when available)
        domain = _get_domain_from_url(str(request.url))
        scraper = await get_scraper(domain=domain)
        
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

            # On navigation failure: test proxy, mark it as failed, and drop domain session
            proxy_test = None
            try:
                if request.use_proxy:
                    proxy_test = await _test_proxy_connectivity(scraper)
            except Exception as proxy_err:
                logger.error(f"❌ Proxy test failed: {proxy_err}")

            try:
                proxy_info = scraper.get_current_proxy_info()
                if proxy_info and "url" in proxy_info:
                    scraper.mark_proxy_failed(proxy_info["url"])
            except Exception as mark_err:
                logger.warning(f"⚠️ Could not mark proxy as failed: {mark_err}")

            try:
                domain = _get_domain_from_url(str(request.url))
                if domain and domain in domain_sessions:
                    domain_sessions.pop(domain, None)
                    logger.info(f"🗑️ Dropped domain session for {domain} due to navigation failure")
            except Exception:
                pass

            try:
                await cleanup_scraper(scraper)
            except Exception:
                pass
            return {
                "success": False,
                "url": str(request.url),
                "error": error_msg,
                "load_time": time.time() - start_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "proxy_used": scraper.get_current_proxy_info() if hasattr(scraper, 'get_current_proxy_info') else None,
                "proxy_test": proxy_test,
            }

        # Wait for element if specified
        if request.wait_for_element:
            logger.info(f"⏳ Waiting for element with timeout: {request.element_timeout}s")
            await asyncio.sleep(request.element_timeout)

        # Wait for page to load and optional wait_time
        try:
            await scraper.page.wait_for_load_state('domcontentloaded', timeout=10000)
        except Exception as e:
            msg = f"DOM content loaded timeout: {str(e)}"
            logger.warning(f"⚠️ {msg}")
            errors.append(msg)
            try:
                current_url = scraper.page.url
                if "about:blank" in current_url or not current_url:
                    error_msg = f"Page failed to load: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    await cleanup_scraper(scraper)
                    return {
                        "success": False,
                        "url": str(request.url),
                        "error": error_msg,
                        "load_time": time.time() - start_time,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "proxy_used": scraper.get_current_proxy_info() if hasattr(scraper, 'get_current_proxy_info') else None,
                    }
            except Exception:
                pass
        
        if request.wait_time:
            logger.info(f"⏳ Waiting {request.wait_time} seconds")
            await asyncio.sleep(request.wait_time)

        # JavaScript'in tam çalışmasını bekle ve sonra HTML'i al
        try:
            await scraper.page.wait_for_function("document.readyState === 'complete'", timeout=10000)
            await asyncio.sleep(1)
        except Exception as e:
            msg = f"DOM stabilizasyonu bekleme hatası: {str(e)}"
            logger.warning(f"⚠️ {msg}")
            errors.append(msg)

        logger.info("🪞 DOM ready for scraping")

        # Debug: save initial screenshot only when debug=true
        if request.debug:
            first_path = await _save_debug_screenshot(
                scraper,
                os.path.join(DEBUG_DIR, f"{request_id}_00_initial.png"),
            )
            if first_path:
                debug_files.append(first_path)

        if request.click:
            logger.info(f"🖱️ Click operations requested: {len(request.click)} clicks")
            await execute_clicks(
                scraper,
                request.click,
                request_id=request_id if request.debug else None,
                errors=errors,
            )
            await asyncio.sleep(0.5)
            logger.info("✅ All click operations completed, proceeding with scraping")

        proxy_info = scraper.get_current_proxy_info()

        response_data = {
            "get": {},
            "collect": {}
        }

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
                    msg = f"Failed to extract '{key}': {str(e)}"
                    logger.error(f"❌ {msg}")
                    errors.append(msg)
                    response_data["get"][key] = ""

        if request.collect:
            logger.info(f"📋 Processing {len(request.collect)} 'collect' operations")
            for key, config in request.collect.items():
                try:
                    selector = config["selector"]
                    fields = config.get("fields", {})
                    items = await unified_parser(scraper, selector, operation_type="collection", fields=fields, debug=request.debug)
                    response_data["collect"][key] = items
                    logger.info(f"✅ Extracted '{key}': {len(items)} items")
                except Exception as e:
                    msg = f"Failed to extract '{key}': {str(e)}"
                    logger.error(f"❌ {msg}")
                    errors.append(msg)
                    response_data["collect"][key] = []
        
        if request.take_screenshot:
            try:
                screenshot_path = await scraper.take_screenshot(request_id)
                logger.info(f"📸 Screenshot saved: {screenshot_path}")
            except Exception as e:
                msg = f"Screenshot failed: {str(e)}"
                logger.error(f"❌ {msg}")
                errors.append(msg)

        if request.extract_links:
            try:
                links = await scraper.extract_links()
                logger.info(f"🔗 Extracted {len(links)} links")
            except Exception as e:
                msg = f"Link extraction failed: {str(e)}"
                logger.error(f"❌ {msg}")
                errors.append(msg)

        if request.debug:
            try:
                debug_html = await scraper.page.content()
                logger.info(f"🔍 Debug HTML: {len(debug_html)} chars")
            except Exception as e:
                msg = f"Debug HTML failed: {str(e)}"
                logger.error(f"❌ {msg}")
                errors.append(msg)
            # Collect all debug files for this request id (screenshots + HTML)
            try:
                _ensure_debug_dir()
                base_url = str(http_request.base_url).rstrip("/") if http_request else ""
                prefix = f"{request_id}_"
                debug_files = sorted(
                    (
                        f"{base_url}/debug/{name}?api_key={api_key}"
                        if base_url
                        else f"/debug/{name}?api_key={api_key}"
                    )
                    for name in os.listdir(DEBUG_DIR)
                    if name.startswith(prefix)
                )
            except Exception:
                debug_files = debug_files or []
        # Store domain session on successful page load
        await _store_domain_session(scraper, str(request.url))

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
            "proxy_used": proxy_info,
            "errors": errors,
        }
        if request.debug:
            if debug_html:
                response["debug_html"] = debug_html
            response["debug_files"] = debug_files
        return response

    except Exception as e:
        load_time = time.time() - start_time
        error_msg = f"Unified scraping failed: {str(e)}"
        logger.error(f"❌ {error_msg}")

        try:
            await cleanup_scraper(scraper)
        except Exception:
            pass

        proxy_info = None
        scraper_var = locals().get('scraper')
        if scraper_var:
            try:
                proxy_info = scraper_var.get_current_proxy_info()
            except Exception:
                pass

        return {
            "success": False,
            "url": str(request.url),
            "error": error_msg,
            "load_time": load_time,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "proxy_used": proxy_info,
        }

async def scrape_legacy(request: ScrapeRequest, api_key: str):
    """Legacy scraping endpoint for backward compatibility"""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    logger.info(f"📡 Legacy scraping request {request_id}: {request.url} (API Key: {api_key[:20]}...)")
    
    try:
        # Get scraper instance (per-domain session + sticky proxy when available)
        domain = _get_domain_from_url(str(request.url))
        scraper = await get_scraper(domain=domain)
        
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

            # On navigation failure: test proxy, mark it as failed, and drop domain session
            proxy_test = None
            try:
                if request.use_proxy:
                    proxy_test = await _test_proxy_connectivity(scraper)
            except Exception as proxy_err:
                logger.error(f"❌ Proxy test failed: {proxy_err}")

            try:
                proxy_info = scraper.get_current_proxy_info()
                if proxy_info and "url" in proxy_info:
                    scraper.mark_proxy_failed(proxy_info["url"])
            except Exception as mark_err:
                logger.warning(f"⚠️ Could not mark proxy as failed: {mark_err}")

            try:
                domain = _get_domain_from_url(str(request.url))
                if domain and domain in domain_sessions:
                    domain_sessions.pop(domain, None)
                    logger.info(f"🗑️ Dropped domain session for {domain} due to navigation failure")
            except Exception:
                pass

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
                "proxy_test": proxy_test,
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
        
        # Store domain session on successful page load
        await _store_domain_session(scraper, str(request.url))

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


@app.get("/debug/{filename}")
async def get_debug_file(
    filename: str,
    api_key: str,
):
    """
    Serve debug files (screenshots & HTML) generated when debug=true.
    `debug_files` entries in responses are URLs pointing to this endpoint.
    """
    # Simple API key check via query parameter
    if api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")

    safe_name = os.path.basename(filename)
    file_path = os.path.join(DEBUG_DIR, safe_name)

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Debug file not found")

    # Inline display: choose media type by extension
    media_type = None
    if file_path.endswith(".png"):
        media_type = "image/png"
    elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
        media_type = "image/jpeg"
    elif file_path.endswith(".html") or file_path.endswith(".htm"):
        media_type = "text/html"

    return FileResponse(file_path, media_type=media_type)

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