"""
Web Scraper Core Module
Playwright-based web scraping with proxy support

Author: Volkan AYDIN
Year: 2025
License: CC BY-NC-SA 4.0 (Non-Commercial)
"""

import asyncio
import time
import json
import random
import os
import socks
import socket
from playwright.async_api import async_playwright
from config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebScraper:
    """Web scraper with proxy support and JavaScript execution"""
    
    def __init__(self):
        self.config = Config()
        self.browser = None
        self.context = None
        self.page = None
        self.proxy_list = []
        self.current_proxy_index = 0
        self.proxy_failures = {}
        self.load_proxy_list()
    
    def load_proxy_list(self):
        """Load proxy list from environment"""
        try:
            if not self.config.PROXY_ENABLED:
                logger.info("Proxy is disabled")
                self.proxy_list = []
                return
                
            if self.config.PROXY_LIST and len(self.config.PROXY_LIST) > 0:
                self.proxy_list = []
                for proxy_item in self.config.PROXY_LIST:
                    if proxy_item.strip():  # Skip empty strings
                        # Parse proxy item - can be URL or URL:username:password format
                        # Check if it contains credentials (more than 2 colons)
                        if proxy_item.count(':') > 2:
                            # Format: http://proxy.com:8080:username:password
                            last_colon = proxy_item.rfind(':')
                            second_last_colon = proxy_item.rfind(':', 0, last_colon)
                            
                            proxy_url = proxy_item[:second_last_colon]
                            credentials_part = proxy_item[second_last_colon + 1:]
                            credentials = credentials_part.split(':')
                            
                            username = credentials[0] if len(credentials) > 0 else ""
                            password = credentials[1] if len(credentials) > 1 else ""
                        else:
                            # Format: http://proxy.com:8080 (no credentials)
                            proxy_url = proxy_item.strip()
                            username = ""
                            password = ""
                        
                        # Determine proxy type from URL
                        proxy_type = "HTTP"
                        if proxy_url.startswith("socks4://"):
                            proxy_type = "SOCKS4"
                            proxy_url = proxy_url.replace("socks4://", "http://")
                        elif proxy_url.startswith("socks5://"):
                            proxy_type = "SOCKS5"
                            proxy_url = proxy_url.replace("socks5://", "http://")
                        elif proxy_url.startswith("http://") or proxy_url.startswith("https://"):
                            proxy_type = "HTTP"
                        
                        proxy_info = {
                            "url": proxy_url,
                            "username": username,
                            "password": password,
                            "country": "Unknown",
                            "type": proxy_type,
                            "status": "working",
                            "speed": "unknown",
                            "last_tested": "2025-01-09"
                        }
                        self.proxy_list.append(proxy_info)
                logger.info(f"Loaded {len(self.proxy_list)} proxies from environment")
            else:
                logger.info("No proxy list found in environment")
                self.proxy_list = []
                
        except Exception as e:
            logger.error(f"Error loading proxy list: {e}")
            self.proxy_list = []
    
    def get_next_proxy(self):
        """Get next working proxy from the list"""
        if not self.config.PROXY_ENABLED:
            return None  # Proxy is disabled
        
        if not self.proxy_list:
            return None  # No proxy available
        
        # Use the current proxy index (set by API)
        if self.current_proxy_index < len(self.proxy_list):
            proxy = self.proxy_list[self.current_proxy_index]
            proxy_url = proxy.get('url', '')
            
            # Check if proxy has too many failures
            if self.proxy_failures.get(proxy_url, 0) < self.config.PROXY_MAX_FAILURES:
                logger.info(f"🔄 Using proxy {self.current_proxy_index + 1}/{len(self.proxy_list)}: {proxy_url}")
                return proxy  # Return full proxy info dict
            else:
                logger.warning(f"⚠️ Proxy {proxy_url} has too many failures, skipping")
        
        # If current proxy failed, try to find any working proxy
        for i, proxy in enumerate(self.proxy_list):
            proxy_url = proxy.get('url', '')
            if self.proxy_failures.get(proxy_url, 0) < self.config.PROXY_MAX_FAILURES:
                logger.info(f"🔄 Fallback to proxy {i + 1}/{len(self.proxy_list)}: {proxy_url}")
                return proxy
        
        # If no working proxy found, return None
        logger.error("❌ No working proxies available")
        return None
    
    def get_current_proxy_info(self):
        """Get current proxy information for response"""
        if not self.config.PROXY_ENABLED or not self.proxy_list:
            return None
        
        if self.current_proxy_index < len(self.proxy_list):
            proxy = self.proxy_list[self.current_proxy_index]
            return {
                "url": proxy.get('url', ''),
                "type": proxy.get('type', 'HTTP'),
                "index": self.current_proxy_index + 1,
                "total": len(self.proxy_list)
            }
        return None
    
    def mark_proxy_failed(self, proxy_url):
        """Mark a proxy as failed"""
        if proxy_url in self.proxy_failures:
            self.proxy_failures[proxy_url] += 1
        else:
            self.proxy_failures[proxy_url] = 1
        logger.warning(f"Proxy {proxy_url} marked as failed (failures: {self.proxy_failures[proxy_url]})")
    
    async def setup_browser(self):
        """Setup browser with proxy configuration"""
        try:
            self.playwright = await async_playwright().start()
            
            # Browser arguments
            browser_args = [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                f'--user-agent={self.config.USER_AGENT}'
            ]
            
            # Proxy configuration
            proxy_config = None
            proxy_info = self.get_next_proxy()
            
            if proxy_info:
                proxy_url = proxy_info.get('url')
                proxy_username = proxy_info.get('username', '')
                proxy_password = proxy_info.get('password', '')
                proxy_type = proxy_info.get('type', 'HTTP')
                
                # Configure proxy based on type
                if proxy_type in ['SOCKS4', 'SOCKS5']:
                    # For SOCKS proxies, we need to set up system-level proxy
                    # Playwright doesn't directly support SOCKS, so we'll use a workaround
                    logger.info(f"Using SOCKS proxy: {proxy_url} (Type: {proxy_type})")
                    
                    # Extract host and port from proxy URL
                    if proxy_url.startswith('http://'):
                        proxy_url = proxy_url.replace('http://', '')
                    
                    if ':' in proxy_url:
                        host, port = proxy_url.split(':', 1)
                        port = int(port)
                    else:
                        host = proxy_url
                        port = 1080  # Default SOCKS port
                    
                    # Set up SOCKS proxy for the entire system
                    if proxy_type == 'SOCKS4':
                        socks.set_default_proxy(socks.SOCKS4, host, port, username=proxy_username, password=proxy_password)
                    elif proxy_type == 'SOCKS5':
                        socks.set_default_proxy(socks.SOCKS5, host, port, username=proxy_username, password=proxy_password)
                    
                    # Monkey patch socket to use SOCKS
                    socket.socket = socks.socksocket
                    
                    # For Playwright, we'll use a different approach
                    # We'll create a custom proxy server or use HTTP tunneling
                    proxy_config = None  # SOCKS proxies handled at system level
                    
                else:
                    # HTTP/HTTPS proxy configuration
                    proxy_config = {
                        'server': proxy_url,
                        'username': proxy_username,
                        'password': proxy_password
                    }
                    logger.info(f"Using HTTP proxy: {proxy_url}")
                    if proxy_username:
                        logger.info(f"Proxy credentials: {proxy_username}")
            else:
                logger.info("No proxy configured, running without proxy")
            
            # Launch browser
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.HEADLESS,
                args=browser_args
            )
            
            # Create context with proxy
            self.context = await self.browser.new_context(
                proxy=proxy_config,
                viewport={'width': 1920, 'height': 1080},
                user_agent=self.config.USER_AGENT
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Set timeout
            self.page.set_default_timeout(self.config.TIMEOUT)
            
            logger.info("Browser setup completed successfully")
            
        except Exception as e:
            logger.error(f"Error setting up browser: {e}")
            raise
    
    async def navigate_to_url(self, url):
        """Navigate to a specific URL"""
        try:
            logger.info(f"Navigating to: {url}")
            await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
            logger.info("Page loaded successfully")
            
            # Wait for JavaScript to load
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            raise
    
    async def wait_for_element(self, selector, timeout=None):
        """Wait for an element to appear on the page"""
        try:
            timeout = timeout or self.config.DEFAULT_WAIT_TIME
            await self.page.wait_for_selector(selector, timeout=timeout)
            logger.info(f"Element found: {selector}")
            return True
        except Exception as e:
            logger.error(f"Element not found: {selector}")
            return False
    
    async def get_element_text(self, selector):
        """Get text content of an element"""
        try:
            element = await self.page.query_selector(selector)
            if element:
                text = await element.text_content()
                return text.strip()
            return None
        except Exception as e:
            logger.error(f"Error getting text for {selector}: {e}")
            return None
    
    async def get_elements_text(self, selector):
        """Get text content of multiple elements"""
        try:
            elements = await self.page.query_selector_all(selector)
            texts = []
            for element in elements:
                text = await element.text_content()
                if text:
                    texts.append(text.strip())
            return texts
        except Exception as e:
            logger.error(f"Error getting texts for {selector}: {e}")
            return []
    
    async def click_element(self, selector):
        """Click on an element"""
        try:
            await self.page.click(selector)
            logger.info(f"Clicked element: {selector}")
            return True
        except Exception as e:
            logger.error(f"Error clicking {selector}: {e}")
            return False
    
    async def fill_input(self, selector, text):
        """Fill an input field"""
        try:
            await self.page.fill(selector, text)
            logger.info(f"Filled input {selector} with: {text}")
            return True
        except Exception as e:
            logger.error(f"Error filling input {selector}: {e}")
            return False
    
    async def execute_javascript(self, script):
        """Execute JavaScript code"""
        try:
            result = await self.page.evaluate(script)
            logger.info("JavaScript executed successfully")
            return result
        except Exception as e:
            logger.error(f"Error executing JavaScript: {e}")
            return None
    
    async def take_screenshot(self, filename="screenshot.png"):
        """Take a screenshot of the current page"""
        try:
            await self.page.screenshot(path=filename)
            logger.info(f"Screenshot saved: {filename}")
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
    
    async def close(self):
        """Close browser and cleanup with robust error handling"""
        errors = []
        
        # Track if browser was already disconnected to skip playwright cleanup
        browser_already_disconnected = False
        
        # Close page with timeout
        if self.page:
            try:
                # Check if page is already closed to avoid errors
                try:
                    if self.page.is_closed():
                        logger.debug("Page already closed")
                    else:
                        await asyncio.wait_for(self.page.close(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("Page close timeout, forcing close")
                    try:
                        if not self.page.is_closed():
                            await self.page.close()
                    except:
                        pass
                except:
                    pass  # If is_closed() fails, try to close anyway
            except Exception as e:
                error_msg = str(e)
                # EPIPE errors are expected when browser process already terminated
                if 'EPIPE' not in error_msg and 'broken pipe' not in error_msg.lower():
                    errors.append(f"Page close error: {e}")
                    logger.error(f"Error closing page: {e}")
            finally:
                self.page = None
        
        # Close context with timeout
        if self.context:
            try:
                await asyncio.wait_for(self.context.close(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Context close timeout, forcing close")
                try:
                    # Try to close anyway - Playwright will handle if already closed
                    await self.context.close()
                except:
                    pass
            except Exception as e:
                error_msg = str(e)
                if 'EPIPE' not in error_msg and 'broken pipe' not in error_msg.lower():
                    errors.append(f"Context close error: {e}")
                    logger.error(f"Error closing context: {e}")
            finally:
                self.context = None
        
        # Close browser with timeout
        if self.browser:
            try:
                # Check if browser is still connected before closing
                try:
                    if not self.browser.is_connected():
                        logger.debug("Browser already disconnected")
                        browser_already_disconnected = True
                    else:
                        await asyncio.wait_for(self.browser.close(), timeout=10.0)
                except asyncio.TimeoutError:
                    logger.warning("Browser close timeout, forcing close")
                    try:
                        if self.browser.is_connected():
                            await self.browser.close()
                    except:
                        pass
                except:
                    pass  # If is_connected() fails, try to close anyway
            except Exception as e:
                error_msg = str(e)
                if 'EPIPE' not in error_msg and 'broken pipe' not in error_msg.lower():
                    errors.append(f"Browser close error: {e}")
                    logger.error(f"Error closing browser: {e}")
            finally:
                self.browser = None
        
        # Stop playwright with timeout (always try, even if browser was disconnected)
        if hasattr(self, 'playwright') and self.playwright:
            try:
                if not browser_already_disconnected:
                    await asyncio.wait_for(self.playwright.stop(), timeout=5.0)
                else:
                    # Browser already disconnected, but still try to stop playwright gracefully
                    try:
                        await asyncio.wait_for(self.playwright.stop(), timeout=2.0)
                    except:
                        pass  # Ignore errors if browser was already disconnected
            except asyncio.TimeoutError:
                logger.warning("Playwright stop timeout")
            except Exception as e:
                error_msg = str(e)
                # EPIPE errors are expected when browser process already terminated
                if 'EPIPE' not in error_msg and 'broken pipe' not in error_msg.lower():
                    errors.append(f"Playwright stop error: {e}")
                    logger.error(f"Error stopping playwright: {e}")
            finally:
                if hasattr(self, 'playwright'):
                    self.playwright = None
        
        if errors:
            logger.warning(f"Browser cleanup completed with {len(errors)} non-critical errors")
        else:
            logger.info("Browser closed successfully")

async def main():
    """Example usage of the scraper"""
    scraper = WebScraper()
    
    try:
        # Setup browser
        await scraper.setup_browser()
        
        # Navigate to a website (example)
        await scraper.navigate_to_url("https://example.com")
        
        # Wait for page to load
        await asyncio.sleep(3)
        
        # Get page title
        title = await scraper.get_element_text("h1")
        print(f"Page title: {title}")
        
        # Take screenshot
        await scraper.take_screenshot("example_screenshot.png")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main()) 