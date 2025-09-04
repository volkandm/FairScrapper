"""
Proxy Tester Module
Tests proxy list from GitHub and finds working proxies

Author: Volkan AYDIN
Year: 2025
License: CC BY-NC-SA 4.0 (Non-Commercial)
"""

import asyncio
import aiohttp
import time
import logging
from typing import List, Dict, Optional
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProxyTester:
    """Tests proxy list and finds working proxies"""
    
    def __init__(self):
        self.test_url = "http://httpbin.org/ip"  # Test URL to check proxy
        self.timeout = 10  # Timeout in seconds
        self.max_workers = 20  # Maximum concurrent connections
        self.working_proxies = []
        
    async def test_proxy(self, session: aiohttp.ClientSession, proxy: str) -> Optional[Dict]:
        """Test a single proxy"""
        try:
            start_time = time.time()
            
            # Test proxy with timeout
            async with session.get(
                self.test_url,
                proxy=f"socks4://{proxy}",
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status == 200:
                    response_time = time.time() - start_time
                    result = await response.json()
                    
                    proxy_info = {
                        "proxy": proxy,
                        "status": "working",
                        "response_time": round(response_time, 2),
                        "ip": result.get("origin", "unknown"),
                        "type": "SOCKS4"
                    }
                    
                    logger.info(f"✅ Working proxy: {proxy} (Response time: {response_time:.2f}s)")
                    return proxy_info
                    
        except Exception as e:
            logger.debug(f"❌ Failed proxy: {proxy} - {str(e)}")
            return None
    
    async def test_proxy_list(self, proxy_list: List[str]) -> List[Dict]:
        """Test multiple proxies concurrently"""
        logger.info(f"Testing {len(proxy_list)} proxies...")
        
        # Limit concurrent connections
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def test_with_semaphore(proxy: str):
            async with semaphore:
                return await self.test_proxy(session, proxy)
        
        async with aiohttp.ClientSession() as session:
            tasks = [test_with_semaphore(proxy) for proxy in proxy_list]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter working proxies
            working_proxies = []
            for result in results:
                if isinstance(result, dict) and result.get("status") == "working":
                    working_proxies.append(result)
            
            return working_proxies
    
    async def download_proxy_list(self) -> List[str]:
        """Download proxy list from GitHub"""
        try:
            # GitHub raw content URL
            url = "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        # Split by lines and filter empty lines
                        proxy_list = [line.strip() for line in content.split('\n') if line.strip()]
                        logger.info(f"Downloaded {len(proxy_list)} proxies from GitHub")
                        return proxy_list
                    else:
                        logger.error(f"Failed to download proxy list: HTTP {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error downloading proxy list: {e}")
            return []
    
    async def find_working_proxies(self, max_working: int = 20, max_test: int = 500) -> List[Dict]:
        """Find working proxies from GitHub list"""
        logger.info("Starting proxy discovery process...")
        
        # Download proxy list
        proxy_list = await self.download_proxy_list()
        if not proxy_list:
            logger.error("No proxies downloaded")
            return []
        
        # Limit the number of proxies to test for faster results
        if len(proxy_list) > max_test:
            proxy_list = proxy_list[:max_test]
            logger.info(f"Testing first {max_test} proxies for faster results")
        
        # Test proxies
        working_proxies = await self.test_proxy_list(proxy_list)
        
        # Sort by response time (fastest first)
        working_proxies.sort(key=lambda x: x.get("response_time", float('inf')))
        
        # Limit to requested number
        if len(working_proxies) > max_working:
            working_proxies = working_proxies[:max_working]
        
        logger.info(f"Found {len(working_proxies)} working proxies")
        return working_proxies
    
    def save_working_proxies(self, proxies: List[Dict], filename: str = "working_proxies.json"):
        """Save working proxies to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(proxies, f, indent=2, ensure_ascii=False)
            logger.info(f"Working proxies saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving proxies: {e}")
    
    def print_proxy_summary(self, proxies: List[Dict]):
        """Print summary of working proxies"""
        if not proxies:
            print("❌ No working proxies found")
            return
        
        print(f"\n✅ Found {len(proxies)} working proxies:\n")
        print(f"{'Proxy':<25} {'Response Time':<15} {'IP':<20} {'Type':<10}")
        print("-" * 70)
        
        for proxy in proxies:
            print(f"{proxy['proxy']:<25} {proxy['response_time']:<15}s {proxy['ip']:<20} {proxy['type']:<10}")
        
        print(f"\nFastest proxy: {proxies[0]['proxy']} ({proxies[0]['response_time']}s)")
        print(f"Slowest proxy: {proxies[-1]['proxy']} ({proxies[-1]['response_time']}s)")

async def main():
    """Main function to test proxies"""
    tester = ProxyTester()
    
    # Find working proxies
    working_proxies = await tester.find_working_proxies(max_working=20, max_test=500)
    
    if working_proxies:
        # Print summary
        tester.print_proxy_summary(working_proxies)
        
        # Save to file
        tester.save_working_proxies(working_proxies)
        
        # Show how to use in config
        print(f"\n📝 To use these proxies in your config.py, add this to your .env file:")
        print("PROXY_LIST=" + ",".join([p['proxy'] for p in working_proxies]))
    else:
        print("❌ No working proxies found. Please try again later.")

if __name__ == "__main__":
    asyncio.run(main())
