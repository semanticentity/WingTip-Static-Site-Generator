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
* SEO optimized with canonical URLs + sitemap.xml
* Open Graph and Twitter meta support
* Dark/light mode toggle with auto detection
* Live dev server with auto-reload (`serve.py`)
* Built-in Open Graph image generator
* GitHub Actions deployment support
* Custom 404 error page handling
* Built-in client-side search ([learn more](docs/search-features.md))

---

## Quickstart

```bash
pip install markdown beautifulsoup4 livereload pillow PyYAML
# Alternatively, using uv (a fast Python package installer)
uv pip install markdown beautifulsoup4 livereload pillow PyYAML
python wingtip/main.py
python wingtip/serve.py
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

- Mermaid diagrams, math rendering, and some advanced Markdown features are not yet supported (planned for a future release).

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

```bash
pip install markdown beautifulsoup4 pillow livereload PyYAML
```

To regenerate code highlight styles:

The file `syntax.css` is generated in `docs/site/` by `main.py` and is the one used by the site. The `pygments.css` file in the root directory might be for reference or manual generation using a command like `pygmentize -S monokai -f html -O full,cssclass=highlight > pygments.css` (using monokai as an example, to match one of the themes).

---

## License

MIT. Use freely. Modify ruthlessly.
