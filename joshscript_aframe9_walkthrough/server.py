#!/usr/bin/env python3
"""
Minimal server for walkthrough folder (uses same CORS handler as main server)
"""
import http.server
import socketserver
import os
from pathlib import Path

PORT = 8002
DIRECTORY = Path(__file__).parent

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

if __name__ == '__main__':
    os.chdir(DIRECTORY)
    print(f"Serving walkthrough at http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()