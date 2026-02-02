#!/usr/bin/env python3
"""
Simple HTTP server for serving the frontend
Binds to 0.0.0.0 to be accessible from Windows
"""
import http.server
import socketserver
import os
import sys

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

if __name__ == '__main__':
    try:
        with socketserver.TCPServer(("0.0.0.0", PORT), MyHTTPRequestHandler) as httpd:
            print(f"Serving HTTP on 0.0.0.0:{PORT}")
            print(f"Dashboard: http://localhost:{PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
