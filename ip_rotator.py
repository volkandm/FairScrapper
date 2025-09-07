#!/usr/bin/env python3
"""
IP Rotator for Tor
Rotates Tor circuits to get new IP addresses

Author: Volkan AYDIN
Year: 2025
"""

import socket
import time
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IPRotator:
    def __init__(self, control_port=9051):
        self.control_port = control_port
        self.proxies = {
            'http': 'socks5://127.0.0.1:9050',
            'https': 'socks5://127.0.0.1:9050'
        }
    
    def get_current_ip(self):
        """Get current IP address through Tor"""
        try:
            response = requests.get('https://httpbin.org/ip', 
                                  proxies=self.proxies, 
                                  timeout=10)
            return response.json().get('origin', 'Unknown')
        except Exception as e:
            logger.error(f"Failed to get IP: {e}")
            return None
    
    def renew_circuit(self):
        """Renew Tor circuit to get new IP"""
        try:
            # Connect to Tor control port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', self.control_port))
            
            # Send commands
            sock.send(b'AUTHENTICATE\r\n')
            response = sock.recv(1024)
            logger.info(f"AUTHENTICATE response: {response.decode().strip()}")
            
            sock.send(b'SIGNAL NEWNYM\r\n')
            response = sock.recv(1024)
            logger.info(f"NEWNYM response: {response.decode().strip()}")
            
            sock.send(b'QUIT\r\n')
            sock.close()
            
            # Wait for circuit to be established
            time.sleep(5)
            return True
            
        except Exception as e:
            logger.error(f"Failed to renew circuit: {e}")
            return False
    
    def rotate_ip(self):
        """Rotate IP and return new IP address"""
        logger.info("🔄 Rotating Tor circuit...")
        
        # Get current IP
        old_ip = self.get_current_ip()
        logger.info(f"📍 Old IP: {old_ip}")
        
        # Renew circuit
        if self.renew_circuit():
            # Get new IP
            new_ip = self.get_current_ip()
            logger.info(f"📍 New IP: {new_ip}")
            
            if old_ip != new_ip:
                logger.info("✅ IP successfully rotated!")
                return new_ip
            else:
                logger.warning("⚠️ IP didn't change, trying again...")
                time.sleep(10)
                return self.get_current_ip()
        else:
            logger.error("❌ Failed to rotate IP")
            return None

def test_rotation():
    """Test IP rotation functionality"""
    rotator = IPRotator()
    
    print("🔍 Testing Tor IP Rotation")
    print("=" * 50)
    
    # Get initial IP
    initial_ip = rotator.get_current_ip()
    print(f"📍 Initial IP: {initial_ip}")
    
    # Rotate IP
    new_ip = rotator.rotate_ip()
    
    if new_ip and new_ip != initial_ip:
        print(f"✅ Success! IP changed from {initial_ip} to {new_ip}")
    else:
        print("❌ IP rotation failed or IP didn't change")
    
    return new_ip

if __name__ == "__main__":
    test_rotation()
