# Live Reload in WingTip

WingTip supports auto-rebuilding and refreshing the browser when files change during local development.

## How It Works
- `serve.py` uses `livereload` to watch for changes in:
  - README.md
  - docs/*.md files
  - template.html
  - main.py
- When a change is detected:
  - It rebuilds the site in a temporary directory first
  - If the build succeeds, it rebuilds in the actual output directory
  - The browser automatically reloads via WebSocket connection
  - Your scroll position is preserved by the livereload client

## Development Mode
- Live reload is automatically enabled when running the development server
- It's disabled in production builds
- The server runs on port 8000 by default

## To Run

```bash
pip install livereload
python wingtip/serve.py
```

Visit http://localhost:8000 to view your docs with live reload enabled.
