#!/usr/bin/env python3
"""
Simple web server to serve the distributed search dashboard
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    # Change to the web directory
    web_dir = Path(__file__).parent
    os.chdir(web_dir)
    
    PORT = 8080
    
    with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
        print(f"🌐 Dashboard server starting on port {PORT}")
        print(f"📁 Serving files from: {web_dir}")
        print(f"🔗 Dashboard URL: http://localhost:{PORT}/dashboard.html")
        print("=" * 50)
        
        # Open browser automatically
        try:
            webbrowser.open(f'http://localhost:{PORT}/dashboard.html')
            print("✅ Browser opened automatically")
        except:
            print("⚠️  Could not open browser automatically")
            print("   Please open: http://localhost:8080/dashboard.html")
        
        print("\n🔄 Server running... Press Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

if __name__ == "__main__":
    main() 