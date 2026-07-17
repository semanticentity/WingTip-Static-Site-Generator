---
title: Migrate to WingTip
description: Move documentation from a hosted platform or another static generator to portable WingTip output.
keywords:
  - documentation migration
  - open source documentation
  - static site generator
category: Getting started
date: 2026-07-17
---

# Migrate to WingTip

Move an existing documentation repository to static output you can inspect, audit, and host anywhere.

## Automated migration

If the source project uses a `docs.json` or `mint.json` configuration, run the importer:

```bash
pip install wingtip
wingtip migrate ./existing-docs --output ./wingtip-docs
```

The importer is **strictly read-only** — the source project is never modified. It writes a new WingTip project containing:

- Every `.md` and `.mdx` page, with nested paths preserved in URLs
- Navigation order (`order` frontmatter) and directory groups (`_category.json`) derived from the source navigation
- Internal links rewritten to portable relative links — Markdown links and raw `href`/`src` attributes, absolute or extensionless, with case-insensitive resolution
- Common MDX components approximated as Markdown (callouts, steps, tabs, cards, images); anything unhandled is inventoried per page
- Site name, description, brand colors, and favicon carried into `config.json` and `theme.json`
- `migration-report.md` — a scored summary of what converted cleanly and what needs manual attention (custom components, dynamic link expressions, suspected broken links in the source, redirects, unmapped navigation, configuration not carried)
- `AGENTS.md` — maintenance instructions for coding agents, so the AI assistant your team already uses can build, verify, and extend the docs (no hosted platform required)

The importer is validated against real public hosted-docs repositories ranging from 46 to over 5,000 pages.

Then preview and iterate:

```bash
cd ./wingtip-docs && wingtip --serve
```

Broad MDX component compatibility and OpenAPI reference generation remain roadmap work; the report lists every affected page. The rest of this guide covers manual migration for repositories without a recognized configuration format.

## What works today

WingTip currently supports:

- A repository `README.md` as the documentation home page
- Markdown files in `docs/`, discovered recursively with nested paths preserved in URLs
- Collapsible sidebar groups from directory structure (`_category.json` for names and ordering)
- YAML frontmatter for titles, descriptions, indexing, social metadata, dates, language, category, and version
- Relative Markdown links, including fragments and query strings
- Local images with responsive variants and lazy loading
- Admonitions, tables, footnotes, definition lists, code highlighting, and KaTeX
- Local search, sitemap, robots directives, RSS, structured data, and AI-readable artifacts
- Static deployment to GitHub Pages or any host that serves ordinary files

## What requires manual work

Plan for manual review when the source repository uses:

- MDX or framework-specific components (the importer flags each affected page)
- Navigation tabs, products, or language switchers (groups map automatically where they align with directories)
- OpenAPI-generated endpoint pages or an interactive API playground
- Platform-managed redirects, authentication, previews, analytics, or access controls
- Server-side features that cannot run from static files

WingTip never silently discards unsupported content — the importer leaves unsupported markup in place and lists it in `migration-report.md`. Use the checklist below and request a migration review when compatibility is uncertain.

## Migration process

### 1. Work on a branch

Keep the current documentation deployment unchanged while validating WingTip.

```bash
git switch -c wingtip-migration
```

### 2. Install WingTip

```bash
pip install "wingtip[serve]"
```

### 3. Prepare the source layout

Retain or create this minimal structure:

```text
your-project/
├── README.md
├── docs/
│   ├── getting-started.md
│   ├── authentication.md
│   └── api.md
├── config.json
├── theme.json
└── favicon.png
```

Nested directories under `docs/` are supported directly — nested paths are preserved in generated URLs, so existing structures can move as-is. Record every old and new URL before changing any filenames.

### 4. Add production metadata

Create `config.json` with the final public URL and project identity:

```json
{
  "base_url": "https://docs.example.com",
  "project_name": "Acme Docs",
  "description": "Documentation for Acme developers.",
  "repo_url": "https://github.com/acme/docs",
  "github": {
    "repo": "acme/docs",
    "branch": "main"
  }
}
```

A local `favicon.png` is optional. WingTip does not insert its own branding when your project does not provide one.

### 5. Build and preview

```bash
wingtip --serve
```

Compare every source page with the preview. Pay particular attention to links, images, code examples, frontmatter, canonical URLs, noindex directives, and custom components.

### 6. Audit the output

When working from this repository, run the post-build auditor:

```bash
python audit_site.py --output docs/site --source .
```

The auditor checks required artifacts, missing local files, unexpected dependency CDNs, conditional PWA icons, and branding leaks.

### 7. Preserve URLs

Create a URL inventory before switching production traffic:

| Existing URL | WingTip URL | Action |
| --- | --- | --- |
| `/getting-started` | `/getting-started.html` | Redirect or preserve at the host |
| `/guides/auth` | `/authentication.html` | Add a permanent redirect |

WingTip does not yet generate platform redirects. Configure permanent redirects at your static host and verify that each destination returns the intended page.

### 8. Validate before cutover

Confirm that:

- Every public source page has a destination
- Existing high-value URLs resolve or permanently redirect
- Internal links and assets load without errors
- Canonicals use the production domain
- Intended public pages appear in `sitemap.xml` and `search_index.json`
- Private, hidden, or obsolete pages are noindexed or excluded
- `llms.txt`, `llms-full.txt`, `feed.xml`, and Markdown alternates are present
- Mobile, keyboard, light-mode, dark-mode, and offline behavior are acceptable
- Analytics and custom scripts are explicitly configured rather than inherited

## Serving your migrated site

WingTip emits ordinary static files, so both common documentation topologies work. Pick one, set `base_url` to match, rebuild, and deploy `docs/site/`.

### Topology A — dedicated docs domain (`docs.example.com`)

Set `"base_url": "https://docs.example.com"` and serve `docs/site/` as the web root.

**GitHub Pages / Netlify / Vercel / Cloudflare Pages:** point the project at the `docs/site` output directory (or publish it from CI) and attach the custom domain in the host's dashboard. No further configuration.

**nginx:**

```nginx
server {
  server_name docs.example.com;
  root /var/www/docs-site;      # contents of docs/site/
  index index.html;
  error_page 404 /404.html;
}
```

**Caddy:**

```caddy
docs.example.com {
  root * /var/www/docs-site
  file_server
  handle_errors {
    rewrite * /404.html
    file_server
  }
}
```

### Topology B — subpath on the main domain (`example.com/docs`)

Set `"base_url": "https://example.com/docs"` — generated URLs, canonicals, feeds, and the service worker all carry the `/docs` prefix — then map that prefix to the static files on your main site's proxy.

**nginx (in the main site's server block):**

```nginx
location /docs/ {
  alias /var/www/docs-site/;    # contents of docs/site/
  index index.html;
  try_files $uri $uri/ /docs/404.html;
}
```

**Caddy:**

```caddy
example.com {
  handle_path /docs/* {
    root * /var/www/docs-site
    file_server
  }
  # ... your main site ...
}
```

**Vercel (`vercel.json` on the main site):**

```json
{ "rewrites": [{ "source": "/docs/:path*", "destination": "https://your-docs-deployment.example/:path*" }] }
```

**Netlify (`_redirects` on the main site):**

```text
/docs/* https://your-docs-deployment.example/:splat 200
```

The subpath topology is the one search engineers usually prefer: documentation authority accrues to the main domain rather than a subdomain. Both are fully supported — the demo site itself runs at a subpath (`/WingTip-Static-Site-Generator/` on GitHub Pages), so every generated URL scheme is exercised there.

## Request a migration review

If the repository is public, submit a [migration review request](https://github.com/semanticentity/WingTip-Static-Site-Generator/issues/new?template=migration.yml). You will receive a structured compatibility assessment covering content, navigation, URLs, assets, metadata, and unsupported constructs.

Do not post private repositories, credentials, customer data, internal URLs, or proprietary content in a public issue. For a private project, provide a sanitized reproduction that preserves the relevant file structure and component patterns.

## Migration guarantee

The current promise is transparency, not automatic parity: supported content should build reproducibly, and unsupported content should be identified before a production cutover. The planned importer will formalize this as both human-readable and JSON migration reports.
