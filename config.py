"""
Configuration Module for Web Scraper
Environment-based configuration management

Author: Volkan AYDIN
Year: 2025
License: CC BY-NC-SA 4.0 (Non-Commercial)
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration settings for the scraper"""
    
    # Proxy settings
    PROXY_ENABLED = os.getenv('PROXY_ENABLED', 'true').lower() == 'true'
    PROXY_ROTATION_ENABLED = os.getenv('PROXY_ROTATION_ENABLED', 'true').lower() == 'true'
    PROXY_MAX_FAILURES = int(os.getenv('PROXY_MAX_FAILURES', '3'))
    PROXY_TEST_INTERVAL = int(os.getenv('PROXY_TEST_INTERVAL', '3600'))
    
    # Proxy list from environment (comma-separated)
    PROXY_LIST = [p.strip() for p in os.getenv('PROXY_LIST', '').split(',') if p.strip()] if os.getenv('PROXY_LIST') else []
    
    # Browser settings
    HEADLESS = os.getenv('HEADLESS', 'false').lower() == 'true'
    TIMEOUT = int(os.getenv('TIMEOUT', '30000'))
    USER_AGENT = os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Default scraping settings
    DEFAULT_WAIT_TIME = int(os.getenv('DEFAULT_WAIT_TIME', '5000'))  # milliseconds
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))