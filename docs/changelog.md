# WingTip Changelog

## [v0.4.0]

### ✨ Features

#### GitHub-Flavored Markdown (GFM)
- Added comprehensive GFM support with markdown-it-py plugins:
  - Task lists with checkboxes
  - Footnotes and references
  - Tables with full styling
  - Strikethrough text
  - Better autolinking
  - Definition lists

#### Math & Diagrams
- Added LaTeX math rendering with KaTeX:
  - Inline math with `$...$`
  - Display math with `$$...$$`
  - Fast client-side rendering
  - See [Math Examples](./math-examples.md)

#### Document Versioning
- Added version management system:
  - CLI support for versioned builds
  - Version selector dropdown in UI
  - Version-aware sitemap and links
  - "Latest" version redirect

#### Plugin System
- Introduced extensible plugin architecture:
  - Custom Python plugins in `plugins/` directory
  - Build process hooks for customization
  - Sample banner plugin included

#### Admonitions
- Added support for admonition blocks:
  - Multiple types (note, warning, danger, tip)
  - Custom styling for each type
  - Full dark mode support

#### Search Enhancements
- Enhanced search functionality:
  - `/` to focus search
  - Arrow keys to navigate results
  - Enter to select
  - Esc to clear
- Added result highlighting in search matches
- Improved search UI with theme integration
- Fixed search index path handling for GitHub Pages

### 🎨 UI & Accessibility
- Comprehensive dark mode support:
  - GFM elements (tables, task lists, footnotes)
  - Admonition blocks with distinct themes
  - KaTeX math expressions
  - Code syntax highlighting
- Enhanced mobile responsiveness:
  - Improved tablet breakpoints (768px)
  - Full-width search on mobile
  - Better nav layout on small screens
- Added ARIA labels and roles for better screen reader support
- Improved nav-container styling and transitions
- Consolidated and optimized CSS

### 🛠 Infrastructure
- Added automatic .md to .html link conversion
- Improved GitHub Pages compatibility
- Enhanced build system for versioned docs
- Optimized asset loading and paths

### 📚 Documentation
- Added new guides:
  - Math rendering examples and usage
  - Versioning system setup
  - Plugin development guide
  - Admonition syntax reference
- Updated existing docs:
  - Search features with keyboard shortcuts
  - Accessibility guidelines
  - Mobile-responsive design
  - Dark mode support


## [v0.3.0]

### ✨ Features
- Added client-side search functionality to allow users to quickly find relevant documentation. See [Search Features](./search-features.md) for more details.
- Implemented various improvements to mobile responsiveness for a better user experience on smaller devices.

### 🛠 Fixes & Improvements
- General stability and performance improvements.

### 📚 Documentation
- Updated roadmap and changelog to reflect recent feature additions and version changes.

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
