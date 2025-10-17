#!/usr/bin/env python3
"""
Simple HTTP server for Floor Plan Viewer
Launches the floor_plan_viewer.html application
"""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

# Configuration
PORT = 8000
HOST = 'localhost'

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler with CORS headers for local development"""
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def log_message(self, format, *args):
        """Custom log format with colors"""
        print(f"[{self.log_date_time_string()}] {format % args}")

def main():
    # Change to parent directory to serve both floor plan viewer and SVG source
    script_dir = Path(__file__).parent
    parent_dir = script_dir.parent  # Go up one level to paul/
    os.chdir(parent_dir)
    
    # Create socket server
    Handler = MyHTTPRequestHandler
    
    try:
        with socketserver.TCPServer((HOST, PORT), Handler) as httpd:
            url = f"http://{HOST}:{PORT}/joshscript_aframe6_floorplanbase/floor_plan_viewer.html"
            
            print("=" * 70)
            print("Floor Plan Viewer Server")
            print("=" * 70)
            print(f"Server running at: {url}")
            print(f"Serving directory: {script_dir}")
            print()
            print("Controls:")
            print("  - Mouse Wheel: Zoom")
            print("  - Middle Click + Drag: Pan")
            print("  - Click: Show coordinates")
            print()
            print("Press Ctrl+C to stop the server")
            print("=" * 70)
            
            # Open browser automatically
            try:
                webbrowser.open(url)
                print(f"\n✓ Opened browser at {url}\n")
            except Exception as e:
                print(f"\n✗ Could not open browser automatically: {e}")
                print(f"Please open this URL manually: {url}\n")
            
            # Start serving
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        print("Server stopped.")
    except OSError as e:
        if e.errno == 48 or e.errno == 10048:  # Address already in use
            print(f"\n✗ Error: Port {PORT} is already in use!")
            print(f"Try closing other applications or use a different port.")
        else:
            print(f"\n✗ Error: {e}")

if __name__ == "__main__":
    main()

