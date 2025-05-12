# WingTip Changelog

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
- Theme toggle, TOC keyboard shortcut (`Alt+D`), and favicon support
