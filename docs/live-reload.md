# Live Reload in WingTip

WingTip includes a development server with automatic rebuild and browser refresh on save. This makes local authoring fast and seamless.

## How It Works

* `wingtip/serve.py` runs a `livereload` server on port 8000
* It watches these files:

  * `README.md`
  * All `docs/*.md`
  * `template.html`
  * `main.py`
* When a change is detected:

  * It runs `main.py` in a temporary output folder first
  * If the build succeeds, it re-runs the actual build
  * If the build fails, the current site is preserved
  * The browser auto-refreshes via WebSocket connection
  * Scroll position is preserved after reload

## Run the Dev Server

```bash
pip install livereload
python wingtip/serve.py
```

This will:

* Open `http://localhost:8000` in your browser
* Rebuild the site automatically when you save `.md` or `.html` files
* Refresh the browser instantly, even retaining scroll

## Notes

* Temporary build directory: `docs/site_tmp`
* Live output directory: `docs/site`
* Scroll restoration is built-in via the injected livereload client
* Errors during rebuild are logged but do not overwrite the current site
