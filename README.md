# WingTip

A minimal static site generator for documentation.

![social-card](social-card.png)

Live demo: [semanticentity.github.io/WingTip-Static-Site-Generator](https://semanticentity.github.io/WingTip-Static-Site-Generator)

WingTip turns a `README.md` and a `docs/` folder into a polished static site — no config required. Write in Markdown, hit build, and ship to GitHub Pages in minutes.

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

---

## Quickstart

```bash
pip install markdown beautifulsoup4 livereload pillow
python wingtip/main.py
python wingtip/serve.py  # (Use this, not python serve.py)
```

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
│   └── pygments.css
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

`.github/workflows/pages.yml`:

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
          pip install markdown Pygments Pillow beautifulsoup4

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
    └── social-card.png
```

---

## Requirements

```bash
pip install markdown beautifulsoup4 pillow livereload
```

To regenerate code highlight styles:

```bash
pygmentize -S default -f html > wingtip/pygments.css
```

---

## License

MIT. Use freely. Modify ruthlessly.
