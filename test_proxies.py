"""
Test Proxy Configuration
Tests if the configured proxies are working

Author: Volkan AYDIN
Year: 2025
License: CC BY-NC-SA 4.0 (Non-Commercial)
"""

import asyncio
import aiohttp
import time
from config import Config

async def test_proxy(proxy: str) -> bool:
    """Test if a proxy is working"""
    try:
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://httpbin.org/ip",
                proxy=f"socks4://{proxy}",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    response_time = time.time() - start_time
                    result = await response.json()
                    print(f"✅ {proxy} - Working (Response time: {response_time:.2f}s, IP: {result.get('origin', 'unknown')})")
                    return True
                    
    except Exception as e:
        print(f"❌ {proxy} - Failed: {str(e)}")
        return False

async def test_all_proxies():
    """Test all configured proxies"""
    config = Config()
    
    print(f"Testing {len(config.PROXY_LIST)} configured proxies...\n")
    
    working_count = 0
    for proxy in config.PROXY_LIST:
        if await test_proxy(proxy):
            working_count += 1
    
    print(f"\n📊 Results: {working_count}/{len(config.PROXY_LIST)} proxies are working")
    
    if working_count > 0:
        print(f"✅ Proxy configuration is working correctly!")
    else:
        print(f"❌ No proxies are working. Please check your configuration.")

if __name__ == "__main__":
    asyncio.run(test_all_proxies())

