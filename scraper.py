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
                        
                        proxy_info = {
                            "url": proxy_url,
                            "username": username,
                            "password": password,
                            "country": "Unknown",
                            "type": "HTTP",
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
        
        if not self.proxy_list or not self.config.PROXY_ROTATION_ENABLED:
            return None  # No proxy available
        
        # Find next working proxy
        attempts = 0
        while attempts < len(self.proxy_list):
            proxy = self.proxy_list[self.current_proxy_index]
            proxy_url = proxy.get('url', '')
            
            # Check if proxy has too many failures
            if self.proxy_failures.get(proxy_url, 0) < self.config.PROXY_MAX_FAILURES:
                self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
                return proxy  # Return full proxy info dict
            
            # Move to next proxy
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
            attempts += 1
        
        # If no working proxy found, return None
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
                
                proxy_config = {
                    'server': proxy_url,
                    'username': proxy_username,
                    'password': proxy_password
                }
                logger.info(f"Using proxy: {proxy_url}")
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
        """Close browser and cleanup"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")

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