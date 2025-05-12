# WingTip

Clean docs that soar. A minimal static site generator for beautiful documentation.

![social-card](social-card.png)

## Features

- Converts `README.md` → `docs/site/index.html`
- Converts all `.md` files in `docs/` → individual `.html` pages
- Adds GitHub "Edit this page" links (customizable)
- Builds sitemap.xml for SEO
- Generates a two-column docs index from your Markdown files
- Supports fenced code blocks with Pygments syntax highlighting
- Adds copy-to-clipboard buttons for each code block
- Light/dark mode toggle with system theme detection
- Responsive navigation with collapsible TOC
- Alt+D keyboard shortcut for TOC toggle
- Automatic scroll position restoration after reload
- Optional live server with auto-regeneration + reload on save

---

## Getting Started

### 1. Install WingTip

```bash
# Clone WingTip into your project
git clone https://github.com/SemanticEntity/WingTip.git

# Install dependencies
pip install markdown beautifulsoup4 watchdog
```

### 2. Set Up Your Docs

```
your-project/
├── README.md           # This becomes your index page
├── docs/              # Create this directory
│   ├── guide.md      # Add your documentation pages
│   └── api.md        # Each .md file becomes a page
└── config.json       # Optional: customize your site
```

Example `config.json`:
```json
{
    "project": "Your Project",
    "description": "Your project description",
    "github": {
        "repo": "username/repo",
        "branch": "main"
    }
}
```

### 3. Generate & Preview

```bash
# Generate site from Markdown
python wingtip/main.py
```

```bash
# Start live dev server (with auto rebuild + reload)
python wingtip/server.py
```

Your site will be generated in `docs/site/` and served at `http://localhost:8000`

### 4. Deploy to GitHub Pages

1. Push your changes to GitHub
2. Go to repo Settings > Pages
3. Set branch to `main` and folder to `/docs/site`
4. Your docs will be live at `username.github.io/repo`!

---

## File Structure

```
.
├── README.md
├── docs/
│   ├── getting-started.md
│   ├── api-guide.md
│   └── ...
├── wingtip/
│   ├── main.py          # Static site generator
│   ├── serve.py        # Live server with auto-regeneration
│   ├── killDocs.sh      # Kills local server (port 8000)
│   ├── template.html    # HTML wrapper template
│   └── pygments.css     # Code highlight theme
```

---

## Output

```
.
├── sitemap.txt
└── docs/site/
    ├── index.html
    ├── getting-started.html
    ├── api-guide.html
    └── ...
```

---

## Light/Dark Theming

* Default styles: [Water.css](https://watercss.kognise.dev)
* Auto-detects system theme
* Toggle via 🌓 switch in the top nav
* Theme state is saved in `localStorage`

---

## Syntax Highlighting

Highlighting is powered by [Pygments](https://pygments.org/) and `codehilite`.
To regenerate the CSS:

```bash
pygmentize -S default -f html > wingtip/pygments.css
```

---

## License

MIT. Use freely, modify ruthlessly.

---

> WingTip: Clean docs that soar. Markdown in → HTML out.
