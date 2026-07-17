# WingTip

**Open-source, SEO-first documentation sites from Markdown.**

![WingTip social card](social-card.png)

[Live demo](https://semanticentity.github.io/WingTip-Static-Site-Generator) · [Source](https://github.com/semanticentity/WingTip-Static-Site-Generator) · [Roadmap](docs/roadmap.md)

WingTip turns a repository `README.md` and `docs/` directory into fast, portable static documentation. It generates crawlable HTML, search and discovery metadata, structured data, machine-readable Markdown artifacts, and an offline-capable site without requiring a hosted documentation platform.

Start with zero configuration, customize when needed, and deploy the generated files anywhere.

---

## Why WingTip

- **Own the output:** Build ordinary HTML, CSS, JavaScript, feeds, and metadata that can be hosted on any static file server.
- **Built for discovery:** Generate canonical URLs, robots directives, sitemap metadata, Open Graph and Twitter cards, `TechArticle` and breadcrumb JSON-LD, RSS, and hreflang alternates.
- **Built for AI retrieval:** Publish `llms.txt`, full concatenated documentation, and a Markdown alternate beside every generated page.
- **No mandatory CDN runtime:** Core styles, scripts, icons, KaTeX, and fonts are vendored into the Python package and copied into the build. External analytics remain opt-in.
- **No imposed branding:** Projects without a favicon receive no WingTip favicon, logo, or generated PWA icons.
- **Zero infrastructure:** Search, navigation, PWA support, and offline fallback work from static hosting.

## Features

### Search, SEO, and machine-readable output

- Per-page `title`, `description`, `keywords`, canonical URL, robots/noindex, language, Open Graph, and Twitter overrides
- Automatic description fallback from the first paragraph
- `TechArticle` and `BreadcrumbList` JSON-LD
- `sitemap.xml`, `robots.txt`, RSS, `llms.txt`, and full concatenated documentation
- Raw Markdown alternates emitted as `.html.md`
- Published/updated dates with Git-based modified-date fallback
- Per-page categories and versions, plus generated `categories.json` and `versions.json`
- Per-page language and translation mappings with `hreflang` and `x-default`
- Local client-side full-text search with keyboard navigation ([details](docs/search-features.md))

### Documentation experience

- `README.md` becomes `index.html`; top-level `docs/*.md` files become standalone pages
- Automatic sidebar, table of contents, and previous/next navigation
- GitHub “Edit this page” links
- Responsive layout with light/dark mode and screen-reader/keyboard support
- Pygments syntax highlighting and copy-to-clipboard controls
- Tables, footnotes, definition lists, attributes, admonitions, and Markdown inside HTML
- KaTeX math rendering ([examples](docs/math-examples.md))
- Configurable external-link handling and correct `.md` link rewriting, including fragments and queries
- Custom Markdown-based `404.html`

### Performance, security, and extensibility

- Local image copying, lazy loading, intrinsic dimensions, and responsive `srcset` generation
- Locally vendored core frontend assets
- PWA manifest, service worker, precache, and offline fallback
- PWA icons generated only from a project-supplied `favicon.png`
- Optional generated or custom Content Security Policy
- Plausible, Umami, Fathom, Google Analytics, custom analytics, and global/per-page `<head>` snippets
- Plugin hooks before/after builds and conversions, plus plugin-provided Python-Markdown extensions
- Theme variables through `theme.json` and static CSS overrides ([theming guide](docs/theming.md))
- Live development server with auto-reload and scroll restoration
- Post-build auditor for missing local files, unexpected CDN references, required artifacts, and branding leaks

---

## Installation

Python 3.9 or newer is required.

```bash
pip install wingtip
```

Install the optional live server:

```bash
pip install "wingtip[serve]"
```

For local development from a clone:

```bash
pip install -e ".[dev]"
```

## Quickstart

Create a project containing `README.md` and, optionally, a `docs/` directory:

```text
your-project/
├── README.md
├── docs/
│   ├── guide.md
│   └── api.md
├── config.json       # optional
├── theme.json        # optional
└── favicon.png       # optional; enables favicon and PWA icon generation
```

Run WingTip from the project directory:

```bash
wingtip
```

The default output is `docs/site`. To build another source directory into a chosen destination:

```bash
wingtip --source ./your-project --output ./build
```

Start the live development server after building:

```bash
wingtip --serve
```

Use `wingtip --help` for all CLI options.

---

## Configuration

Configuration is optional. Without `config.json`, WingTip derives the project name from the `README.md` heading or source-directory name and uses relative URLs for local portability.

Add `config.json` when you want production URLs, repository links, analytics, security policy, or social-card customization:

```json
{
  "base_url": "https://docs.example.com",
  "project_name": "Acme API",
  "version": "1.0.0",
  "description": "Integration documentation for the Acme API.",
  "author": "Acme",
  "repo_url": "https://github.com/acme/api-docs",
  "og_image": "social-card.png",
  "twitter_handle": "@acme",
  "github": {
    "repo": "acme/api-docs",
    "branch": "main"
  },
  "analytics": {
    "provider": "plausible",
    "domain": "docs.example.com"
  },
  "csp": true,
  "social_card": {
    "title": "Acme API",
    "tagline": "Build with Acme.",
    "theme": "light",
    "font": "Poppins"
  }
}
```

Place a local `favicon.png` in the project root to emit favicon/nav-logo markup and generate 192×192 and 512×512 PWA icons. If it is absent, WingTip emits none of those branded assets.

### Per-page frontmatter

Use YAML frontmatter to control individual pages:

```yaml
---
title: Authentication API
description: Authenticate server-side requests to the Acme API.
keywords:
  - API authentication
  - OAuth
canonical: https://docs.example.com/authentication
noindex: false
author: Acme Developer Relations
date: 2026-07-16
lastmod: 2026-07-17
category: API reference
version: v2
lang: en
translations:
  es: https://docs.example.com/es/authentication
og_title: Acme API authentication
twitter_description: Implement Acme API authentication.
---
```

Noindexed pages are excluded from the sitemap, search index, category/version indexes, and structured data.

## Plugins and custom Markdown

Place Python modules in `plugins/`. WingTip can auto-load every module or load only names listed in the `plugins` array in `config.json`.

Plugins can expose:

- `before_build(config, output_dir)`
- `before_convert(frontmatter, markdown, input_path, output_path)`
- `after_convert(html, frontmatter, input_path, output_path)`
- `after_build(config, output_dir)`
- `markdown_extensions`, as a list or callable returning Python-Markdown extensions

Hook failures are reported as warnings so one extension does not silently stop the entire build.

## Build auditing

The repository includes a post-build auditor used by CI:

```bash
python audit_site.py --output docs/site --source .
```

It exits non-zero when it finds:

- Missing local files referenced by generated HTML
- Known CDN origins for dependencies that WingTip vendors locally
- Missing required search, SEO, feed, or PWA artifacts
- Missing PWA icons when a project favicon was supplied
- Output assets byte-identical to packaged branding assets
- WingTip branding in a project whose configured name is not WingTip

CI also runs a negative fixture that deliberately injects a broken asset reference and verifies that the auditor fails.

---

## GitHub Pages deployment

The included GitHub Actions workflow builds and deploys on pushes to `main`. For another repository, the essential build steps are:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- run: pip install wingtip
- run: wingtip
- uses: actions/upload-pages-artifact@v3
  with:
    path: docs/site
```

Set `base_url` to the final Pages URL so canonical, sitemap, feed, social, and alternate URLs are absolute in production.

---

## Social cards

WingTip generates `social-card.png` during a build. Force regeneration after changing card settings:

```bash
wingtip --regen-card
```

The `social_card` object supports title, tagline, light/dark style, font, and an optional logo. Per-page `og_image` and `twitter_image` frontmatter can override the site image.

---

## Custom 404 page

Create `404.md` in the project root. WingTip converts it to `404.html` with the same Markdown processing and site template as other pages:

```markdown
---
permalink: /404.html
noindex: true
---

# Page not found

The requested documentation page does not exist.
```

---

## Generated output

A normal build includes:

```text
docs/site/
├── index.html
├── guide.html
├── guide.html.md
├── search_index.json
├── sitemap.xml
├── robots.txt
├── feed.xml
├── llms.txt
├── llms-full.txt
├── manifest.json
├── sw.js
├── offline.html
├── social-card.png
├── syntax.css
└── static/
```

`categories.json` and `versions.json` are emitted when pages declare those values. `favicon.png`, `icon-192.png`, and `icon-512.png` are emitted only when the project supplies a favicon.

## Current limitations and roadmap

WingTip currently processes `README.md` and top-level `docs/*.md`; nested documentation trees and grouped/collapsible navigation remain roadmap work. Mermaid diagrams, broad MDX compatibility, and a theme marketplace are not yet built.

See the [roadmap and feature comparison](docs/roadmap.md) for planned work.

---

## License

MIT. Use freely. Modify ruthlessly.
