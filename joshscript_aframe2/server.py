#!/usr/bin/env python3
"""
Simple HTTP Server for 360° Navigation System
Serves the A-Frame application with proper CORS headers
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# Configuration
PORT = 8000
DIRECTORY = Path(__file__).parent

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP Request Handler with CORS support"""
    
    def end_headers(self):
        """Add CORS headers to all responses"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight"""
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        """Custom log format with colors"""
        message = format % args
        if '200' in message:
            color = '\033[92m'  # Green
        elif '404' in message:
            color = '\033[91m'  # Red
        else:
            color = '\033[94m'  # Blue
        
        print(f"{color}[{self.log_date_time_string()}] {message}\033[0m")

def main():
    """Start the web server"""
    # Change to the directory containing this script
    os.chdir(DIRECTORY)
    
    print("\n" + "="*60)
    print("360° Cone-Based Navigation System - Development Server")
    print("="*60)
    print(f"\nDirectory: {DIRECTORY}")
    print(f"Port: {PORT}")
    print(f"\n\033[92m✓ Server running at: http://localhost:{PORT}\033[0m")
    print(f"\n\033[93mPress Ctrl+C to stop the server\033[0m")
    print("="*60 + "\n")
    
    # Check for required files
    required_files = ['index.html', 'navigation-system.js', 'styles.css', 'cone_data.json']
    missing_files = []
    
    for filename in required_files:
        if not (DIRECTORY / filename).exists():
            missing_files.append(filename)
    
    if missing_files:
        print(f"\n\033[91m⚠ Warning: Missing files: {', '.join(missing_files)}\033[0m\n")
    
    # Create panoramas directory if it doesn't exist
    panoramas_dir = DIRECTORY / 'panoramas'
    if not panoramas_dir.exists():
        panoramas_dir.mkdir(exist_ok=True)
        print(f"\033[93m→ Created 'panoramas' directory for 360° images\033[0m")
        print(f"  Place your panorama images here (e.g., frame_001.jpg)\n")
    
    # Start server
    try:
        with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n\033[93m⚠ Server stopped by user\033[0m")
        print("="*60 + "\n")
        sys.exit(0)
    except OSError as e:
        if e.errno == 48 or e.errno == 98:  # Address already in use
            print(f"\n\033[91m✗ Error: Port {PORT} is already in use\033[0m")
            print(f"  Try using a different port or stop the other server\n")
        else:
            print(f"\n\033[91m✗ Error: {e}\033[0m\n")
        sys.exit(1)

if __name__ == "__main__":
    main()



