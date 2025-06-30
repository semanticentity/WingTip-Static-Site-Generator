#!/usr/bin/env python3

# serve.py - Development server for WingTip

import os
import sys
import shutil
import subprocess
import webbrowser
from pathlib import Path
import tornado.ioloop
import tornado.web
import tornado.autoreload

# Get absolute paths
BASE_DIR = Path(__file__).parent
SITE_DIR = Path("docs") / "site"
PORT = 8000

def build_site():
    """Build the site and return True if successful"""
    print("\n🔨 Building site...")
    
    try:
        # Try building in a temporary directory first
        tmp_dir = "docs_site_tmp"
        os.makedirs(tmp_dir, exist_ok=True)
        result = subprocess.run(
            ["python", str(BASE_DIR / "main.py"), "--output", tmp_dir],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("  ✓ Build successful")
            # If successful, rebuild for real
            result = subprocess.run(
                ["python", str(BASE_DIR / "main.py")],
                capture_output=True,
                text=True
            )
            return True
        else:
            print("  ✗ Build failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"  ✗ Build error: {e}")
        return False
    finally:
        # Clean up temp dir
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

# Custom handler for serving files and handling 404 errors
class MainHandler(tornado.web.RequestHandler):
    def initialize(self, root_path):
        self.root_path = root_path
        
    def get(self, path):
        # Default to index.html if no path is specified
        if not path:
            path = "index.html"
        
        # Add .html extension if not present and not a directory
        if not path.endswith(".html") and not path.endswith("/") and \
           not os.path.isdir(os.path.join(self.root_path, path)):
            path = path + ".html"
            
        file_path = os.path.join(self.root_path, path)
        
        # If it's a directory, look for index.html
        if os.path.isdir(file_path):
            file_path = os.path.join(file_path, "index.html")
            
        # If the file exists, serve it
        if os.path.exists(file_path) and os.path.isfile(file_path):
            with open(file_path, "rb") as f:
                content = f.read()
            
            # Set content type based on file extension
            if file_path.endswith(".html"):
                self.set_header("Content-Type", "text/html")
            elif file_path.endswith(".css"):
                self.set_header("Content-Type", "text/css")
            elif file_path.endswith(".js"):
                self.set_header("Content-Type", "application/javascript")
            elif file_path.endswith(".png"):
                self.set_header("Content-Type", "image/png")
            elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
                self.set_header("Content-Type", "image/jpeg")
            
            self.write(content)
        else:
            # File not found, serve 404 page
            self.set_status(404)
            error_page = os.path.join(self.root_path, "404.html")
            if os.path.exists(error_page):
                with open(error_page, "rb") as f:
                    self.write(f.read())
            else:
                self.write("<html><head><title>404: Not Found</title></head><body>404: Not Found</body></html>")

def make_app():
    site_path = str(SITE_DIR.absolute())
    return tornado.web.Application([
        # Serve static files directly
        (r"/(.+\.(css|js|png|jpg|jpeg|gif|ico|txt|json))", tornado.web.StaticFileHandler, {"path": site_path}),
        # Main handler for HTML files and 404s
        (r"/(.*)", MainHandler, {"root_path": site_path}),
    ], debug=True)

def watch_files():
    """Watch files for changes and rebuild the site"""
    for pattern in ["README.md", "docs/*.md", "template.html", "main.py", "404.md", "theme.json", "config.json"]:
        tornado.autoreload.watch(pattern)
    
    # Add a callback to rebuild the site
    def rebuild_callback():
        build_site()
    
    tornado.autoreload.add_reload_hook(rebuild_callback)

if __name__ == "__main__":
    print("Building site and starting dev server...")
    
    # Initial build
    if not build_site():
        print("Initial build failed. Fix errors and try again.")
        sys.exit(1)
    
    # Create application
    app = make_app()
    
    # Watch for file changes
    watch_files()
    
    # Start server
    app.listen(PORT)
    print(f"\n🌐 Starting server at http://localhost:{PORT}")
    print(f"   Custom 404 page handling is enabled")
    
    # Open browser only on initial start, not on reloads
    # Create a flag file to track if browser has been opened
    browser_flag_file = Path(".browser_opened")
    
    def open_browser():
        if not browser_flag_file.exists():
            try:
                webbrowser.open(f"http://localhost:{PORT}")
                # Create flag file to prevent reopening
                browser_flag_file.touch()
            except Exception as e:
                print(f"Warning: Could not open browser: {e}")
    
    # Open browser in a separate thread to avoid blocking
    import threading
    threading.Timer(0.5, open_browser).start()
    
    print("\nServer is ready! Press Ctrl+C to stop.")
    
    # Start event loop
    tornado.ioloop.IOLoop.current().start()
