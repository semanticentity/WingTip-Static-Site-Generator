#!/usr/bin/env python3

# serve.py - Development server for WingTip

import os
import sys
import shutil
import subprocess
import webbrowser
from pathlib import Path
from livereload import Server

# Get absolute paths
BASE_DIR = Path(__file__).parent
SITE_DIR = BASE_DIR / "docs" / "site"
PORT = 8000

def build_site():
    """Build the site and return True if successful"""
    print("\n🔨 Building site...")
    # Always run from the correct directory
    os.chdir(str(BASE_DIR))
    
    try:
        # Try building in a temporary directory first
        tmp_dir = "docs/site_tmp"
        os.makedirs(tmp_dir, exist_ok=True)
        result = subprocess.run(
            ["python", "main.py", "--output", tmp_dir],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("  ✓ Build successful")
            # If successful, rebuild for real
            result = subprocess.run(
                ["python", "main.py"],
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

if __name__ == "__main__":
    print("Building site and starting dev server...")
    
    # Initial build
    if not build_site():
        print("Initial build failed. Fix errors and try again.")
        sys.exit(1)
    
    # Create server
    server = Server()
    
    # Watch for changes
    server.watch("README.md", build_site)
    server.watch("docs/*.md", build_site)
    server.watch("template.html", build_site)
    server.watch("main.py", build_site)
    
    # Serve the site
    print(f"\n🌐 Starting server at http://localhost:{PORT}")
    server.serve(port=PORT, root=str(SITE_DIR), open_url_delay=1)
