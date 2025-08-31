#!/usr/bin/env python3
"""
Simple HTTP File Server
Development server for testing web scraping

Author: Volkan AYDIN
Year: 2025
License: CC BY-NC-SA 4.0 (Non-Commercial)
"""

import http.server
import socketserver
import os
import sys

# Define the port
PORT = 8000

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        super().__init__(*args, directory=SCRIPT_DIR, **kwargs)
    
    def do_GET(self):
        # If root path is requested, serve b.html
        if self.path == '/' or self.path == '':
            self.path = '/b.html'
        
        # Call the parent method to handle the request
        return super().do_GET()

def start_server():
    """Start the HTTP server"""
    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print(f"Server starting on port {PORT}")
            print(f"Serving files from: {SCRIPT_DIR}")
            print(f"Access the server at: http://localhost:{PORT} (or your domain)")
            print(f"Press Ctrl+C to stop the server")
            
            # Check if b.html exists
            html_file = os.path.join(SCRIPT_DIR, 'b.html')
            if os.path.exists(html_file):
                print(f"✓ b.html found and ready to serve")
            else:
                print(f"⚠ Warning: b.html not found in {SCRIPT_DIR}")
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"Error: Port {PORT} is already in use")
            print("Please try a different port or stop the service using that port")
        else:
            print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_server()
