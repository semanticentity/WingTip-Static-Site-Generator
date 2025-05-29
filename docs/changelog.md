# WingTip Changelog

## [v0.2.0]

### ✨ Features
- Added support for custom 404 pages: Users can create a `404.md` in the project root, which will be converted to `docs/site/404.html` and included in the sitemap.

### 🛠 Fixes & Improvements
- Corrected path handling in `main.py` and `serve.py` to ensure proper functionality when WingTip is used as a nested module (e.g., running `python wingtip/main.py` from a parent project directory).
- Refined `killDocs.sh` script:
    - Now attempts a graceful process termination (SIGTERM) before resorting to a forceful one (SIGKILL).
    - Removed obsolete PID file handling logic.
- Removed an unused internal function (`write_docs_index`) from `main.py`.
- Removed a duplicate inclusion of `clipboard.js` in `template.html`.

### 📚 Documentation
- Updated `README.md` to accurately reflect nested project structure usage (e.g., `wingtip/main.py` for commands and file paths).
- Clarified `syntax.css` (generated) vs. `pygments.css` (manual reference) in `README.md`.
- Corrected the GitHub Actions workflow example in `README.md` to use `python wingtip/main.py`.
- Added `uv` pip install instructions as an alternative in `README.md`.
- Documented the new custom 404 page feature in `README.md`.
- Documented how to stop the development server (Ctrl+C) and the purpose/usage of `killDocs.sh` in `README.md`.
- Corrected `main.py` help text for sitemap generation and removed outdated notes.
- Removed mention of a non-implemented "TOC keyboard shortcut (`Alt+D`)" from this changelog (v0.1.0 entry).

## [v0.1.0](#v010)

### ✨ Features
- Converts `README.md` and `docs/*.md` to static HTML
- Dark/light mode with system theme detection
- Slideout nav with project logo
- Code syntax highlighting for both themes
- Copy-to-clipboard buttons for all code blocks
- Previous/next navigation links
- GitHub "Edit this page" links
- SEO optimization with meta tags and `sitemap.xml`
- Built-in Open Graph social card generator (via Pillow)
- Live reload development server with scroll state preservation
- GitHub Actions workflow for automatic Pages deployment
- Configurable `favicon`, `og_image`, and `twitter_handle` in `config.json`

### 🛠 Technical
- Markdown to HTML conversion with Pygments highlighting
- Clean Python codebase with minimal dependencies
- JSON config with fallback defaults
- CLI support for `--output` and `--regen-card`
- Auto social card fallback and copy to root if `og_image` is unset
- Auto-download of Google Fonts for social card rendering
- Customizable navigation + dynamic Table of Contents

### 📚 Documentation
- Full quickstart and config guide
- GitHub Pages deployment with prebuilt `pages.yml`
- Example `config.json` for SEO and appearance
- Theme toggle and favicon support
