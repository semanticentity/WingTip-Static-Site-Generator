# WingTip

A minimal static site generator for documentation.

![social-card](social-card.png)

Live demo: [semanticentity.github.io/WingTip-Static-Site-Generator](https://semanticentity.github.io/WingTip-Static-Site-Generator)

WingTip turns a `README.md` and a `docs/` folder into a polished static site — no config required, now with built-in client-side search. Write in Markdown, hit build, and ship to GitHub Pages in minutes.

---

## Features

* Converts `README.md` → `index.html`
* Converts `docs/*.md` → standalone `.html` pages
* Adds GitHub "Edit this page" links
* Responsive sidebar + TOC toggle
* Pygments syntax highlighting for code blocks
* Copy-to-clipboard on all code snippets
* **Full GitHub-Flavored Markdown (GFM) support** (tables, task lists, strikethrough, etc.)
* **LaTeX-style math rendering** (via KaTeX)
* **Admonition blocks** (notes, warnings, tips, etc.)
* SEO optimized with canonical URLs + sitemap.xml
* Open Graph and Twitter meta support
* **Comprehensive dark/light mode:** Auto-detects system preference with manual toggle, now with full support for GFM elements, admonitions, and math rendering (KaTeX) in both themes.
* Live dev server with auto-reload (`serve.py`)
* Built-in Open Graph image generator
* GitHub Actions deployment support
* Custom 404 error page handling
* Built-in client-side search ([learn more](docs/search-features.md))
* **Document versioning support**
* **Basic plugin system** for custom extensions

---

## Quickstart

WingTip now uses `markdown-it-py` for Markdown processing. Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
# Alternatively, using uv (a fast Python package installer)
uv pip install -r requirements.txt

# To build the default documentation (often from ./docs into ./docs/site):
python main.py

# To serve locally (usually serves content from ./docs/site):
python serve.py
```

To stop the development server, press `Ctrl+C` in the terminal where it's running.

If you encounter issues stopping the server or suspect orphaned processes, a utility script `killDocs.sh` is provided in the `wingtip` directory. From your project root, you can run it using:

```bash
bash wingtip/killDocs.sh
```
This script will attempt to forcefully stop any processes related to the WingTip development server.

Then open [http://localhost:8000](http://localhost:8000)

You can change the output folder with `--output`. See `python wingtip/main.py --help` for all CLI options.

---

## File Structure

```
your-project/
├── README.md            # Becomes index.html
├── docs/                # Additional Markdown files
│   ├── guide.md
│   └── api.md
├── wingtip/             # Generator source
│   ├── main.py
│   ├── serve.py
│   ├── generate_card.py
│   ├── template.html
├── pygments.css
└── config.json          # Required if using social cards or favicon (see below)
```

---

## Configuration

A `config.json` file is required if you use social cards or a custom favicon. It is also recommended for SEO and deployment. Fields marked optional can be omitted if not needed.

To generate SEO-friendly output and enable GitHub deployment, add a `config.json` file in the project root:

```json
{
  "base_url": "https://yourusername.github.io/yourrepo",
  "project_name": "WingTip",
  "version": "0.1.0",
  "description": "Minimal static site generator for GitHub Pages",
  "author": "Your Name",
  "repo_url": "https://github.com/yourusername/yourrepo",
  "og_image": "social-card.png",
  "favicon": "https://yourcdn.com/favicon.png",
  "twitter_handle": "@yourhandle",
  "github": {
    "repo": "yourusername/yourrepo",
    "branch": "main"
  },
  "social_card": {
    "title": "WingTip",
    "tagline": "Make your docs fly.",
    "theme": "light",
    "font": "Poppins",
    "image": "social-card.png"
  }
}
```

---

## GitHub Pages Deployment (via Actions)

WingTip includes a GitHub Actions workflow that builds and deploys your site automatically when you push to the `main` branch.

### Setup

1. Push your repository to GitHub
2. Ensure Pages is enabled under **Settings > Pages**
3. Add your `config.json` with a correct `base_url`
4. Your documentation will deploy to:
   `https://yourusername.github.io/yourrepo/`

### Included Workflow

`.github/workflows/static.yml`:

```yaml
name: Deploy static content to Pages

on:
  push:
    branches: ["main"]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  deploy:
    environment:
      name: Pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install markdown Pygments Pillow beautifulsoup4 PyYAML

      - name: Build site
        run: python main.py

      - name: Setup Pages
        uses: actions/configure-pages@v5

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: docs/site

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

---

## Social Card

Generate a shareable Open Graph image:

```bash
python wingtip/main.py --regen-card
```

- This command requires a properly configured `config.json` (with a `social_card` section and related fields).
- Output: `docs/site/social-card.png`
- If no `og_image` is set in your config, the social card will also be copied to `./social-card.png` in the project root.
- Values pulled from `config.json`: supports title, tagline, theme, font, and emoji or image.

---

## Custom 404 Page

WingTip supports a custom "Page Not Found" page that works both locally during development and when deployed to GitHub Pages. To use this feature:

1. Create a `404.md` file in the root of your project directory (the same directory where your `README.md` and `config.json` are located).

2. Add the following YAML front matter at the top of your 404.md file (this is required for GitHub Pages):

```
permalink: /404.html
```
   
   Note: In the actual 404.md file, this should be wrapped with triple-dash lines, but we're omitting them here to avoid breaking the markdown formatting.

3. Write your desired content for the 404 page in Markdown format below the front matter.
   * The title for the generated `404.html` page will be taken from the first H1 heading (e.g., `# Page Not Found`) in your `404.md`.
   * If no H1 heading is found, the title will default to "404.md".

4. When you build your site with `python main.py`, WingTip will automatically:
   * Detect `404.md` and process its front matter
   * Convert it into a `404.html` file in your output directory (e.g., `docs/site/404.html`)
   * Apply the same template and styling as your other pages

5. During local development with `python serve.py`:
   * The development server will automatically serve your custom 404 page when a non-existent URL is accessed
   * This allows you to preview and test your 404 page locally

6. When deployed to GitHub Pages:
   * GitHub Pages will automatically use your custom 404.html file for any non-existent URLs
   * The permalink in the front matter ensures proper routing

This implementation ensures a consistent user experience both during development and in production.

---

## Theming and UX

* Auto light/dark theme based on system preference
* Manual toggle in navigation bar
* Sidebar navigation with collapsible TOC
* Scroll position preserved during live reload

---

## Limitations & Roadmap

- Mermaid diagrams are not yet supported (planned for a future release).
- Advanced plugin features (e.g., event bus, more hook points) are under consideration.

Many initial roadmap items like GFM, Math Rendering, Versioning, basic Plugins, and Admonitions have now been implemented!

---

## Key Features Details

### GitHub-Flavored Markdown (GFM)

WingTip uses `markdown-it-py` with relevant plugins to provide comprehensive GFM support, including:
- Tables
- Task lists (e.g., `- [x] Done`, `- [ ] ToDo`)
- Strikethrough (e.g., `~~deleted text~~`)
- Autolinks
- And more.

### Math Rendering (KaTeX)

Embed LaTeX-style mathematical expressions directly into your Markdown.
- **Inline math:** Wrap your math with single dollar signs: `$E = mc^2$` renders as $E = mc^2$.
- **Display math:** Wrap your math with double dollar signs: `$$\sum_{i=1}^n i = \frac{n(n+1)}{2}$$` renders as:
  $$\sum_{i=1}^n i = \frac{n(n+1)}{2}$$
KaTeX is fast and supports a large subset of LaTeX.

### Admonitions

Highlight special sections of your documentation using admonition blocks. Syntax:

```markdown
!!! note
    This is a note. Useful for highlighting important information.

::: warning Title of Warning
This is a warning with a custom title. Use this for cautionary advice.

!!! danger "Danger Zone"
    Critical information or actions that could have negative consequences.

!!! tip
    A helpful tip or suggestion.

!!! info
    General information block.
```
Supported types typically include `note`, `warning`, `danger`, `error`, `tip`, `hint`, `info`, `seealso`, and more, each with distinct styling.

### Document Versioning

WingTip supports building and browsing multiple versions of your documentation.
- **Structure:** Place different versions of your Markdown source files in subdirectories, e.g., `docs_src_versions/v1.0/`, `docs_src_versions/v0.9/`.
- **Build Process:** The `build_all_versions.py` script orchestrates the build. It scans for version directories, then calls `main.py` for each version, specifying input and output paths (e.g., outputting to `docs/site/v1.0/`, `docs/site/v0.9/`).
- **Version Selector:** The UI includes a dropdown menu to easily switch between built versions.
- **"Latest" Version:** `build_all_versions.py` creates a redirect at the site root (`docs/site/index.html`) to point to the most recent version.
- See `docs/versioning.md` for more details. (This file will be created in a subsequent step).

### Plugin System

Extend WingTip's functionality with custom Python code.
- **Directory:** Place your plugin files (e.g., `my_plugin.py`) in the `plugins/` directory at the project root.
- **Hooks:** Plugins can implement specific functions (hooks) that WingTip will call at different stages of the build process:
    - `before_markdown_conversion(md_content, metadata, filepath)`
    - `after_html_generation(html_content, metadata, filepath)`
    - `after_full_page_assembly(final_html, metadata, output_filepath)`
- **Sample:** A `plugins/sample_banner_plugin.py` is provided to demonstrate how to add a banner to every page.
- See `docs/plugins.md` for more details. (This file will be created in a subsequent step).


---

## Build Output

```
.
├── sitemap.xml
├── robots.txt
└── docs/site/
    ├── index.html
    ├── guide.html
    ├── api.html
    ├── 404.html
    └── social-card.png
```

---

## Requirements

Install all dependencies using:
```bash
pip install -r requirements.txt
```
Core dependencies include `markdown-it-py`, `mdit-py-plugins`, `Pygments`, `BeautifulSoup4`, `PyYAML`, `Pillow`, and `livereload`.

To regenerate code highlight styles:

The file `syntax.css` is generated in `docs/site/` by `main.py` and is the one used by the site. The `pygments.css` file in the root directory might be for reference or manual generation using a command like `pygmentize -S monokai -f html -O full,cssclass=highlight > pygments.css` (using monokai as an example, to match one of the themes).

---

## License

MIT. Use freely. Modify ruthlessly.
