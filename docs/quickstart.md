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
├── README.md         # Your existing README becomes the index
└── docs/            # Create this directory
    └── guide.md     # Add .md files for documentation
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

## 4. Generate & Preview (10s)

```bash
# Generate the site
python wingtip/main.py

# Start dev server with live reload
python wingtip/server.py
```

Your site is now live at `http://localhost:8000` 🚀

## 5. Deploy to GitHub Pages (1 min)

1. Push your changes to GitHub
2. Go to repo Settings > Pages
3. Set branch to `main` and folder to `/docs/site`
4. Your docs are live at `username.github.io/repo`!

***That's it!***

Your documentation now has:
- ✨ Beautiful responsive design
- 🌓 Dark/light mode
- 📱 Mobile-friendly navigation
- 🔍 SEO optimization
- ⚡️ Fast load times
- 🔄 Live preview as you write
- 📝 GitHub edit links

No complex build chain. No configuration needed. Just write Markdown and ship.
