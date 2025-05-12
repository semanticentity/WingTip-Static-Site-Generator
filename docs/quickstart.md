# Quick Start

Add beautiful documentation to your project in under 5 minutes.

## 1. Install WingTip (2 min)

```bash
# In your project directory:
git clone https://github.com/SemanticEntity/WingTip.git
pip install -r WingTip/requirements.txt
```

## 2. Add Your Docs (1 min)

```
your-project/
├── README.md         # Becomes the homepage
└── docs/             # Add .md files for documentation
    └── guide.md
```

## 3. Configure (Optional, 30s)

Create `config.json` in your project root:

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

## 4. Generate and Preview (10s)

```bash
python wingtip/main.py          # Build the site
python wingtip/serve.py         # Start local dev server with live reload
```

Visit `http://localhost:8000` in your browser.

## 5. Deploy to GitHub Pages (1 min)

1. Push your changes to GitHub
2. Go to **Settings → Pages**
3. Set branch to `main` and folder to `/docs/site`
4. Your documentation will be published to `https://username.github.io/repo`

---

Your docs now include:

* Responsive layout with light/dark mode
* Mobile-friendly sidebar and TOC
* SEO-optimized output and social cards
* GitHub "Edit this page" links
* Instant preview with live reload

No build tools. No config lock-in. Just Markdown in, HTML out.
