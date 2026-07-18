# WingTip Changelog

## [v0.6.5] - 2026-07-18

### Redirects

- `config.json` accepts `"redirects": [{"from": "/old-path", "to": "/new-path"}]`. Every build emits a static redirect page per rule (instant redirect with a visible fallback link — works on GitHub Pages and any static host) plus a `_redirects` file in Netlify/Cloudflare Pages format. Platform wildcard patterns (`:slug*`) are translated to splats and covered host-level. Redirect stubs are `noindex` and stay out of the sitemap and search index; collisions with real pages and missing targets warn at build time.
- `wingtip migrate` carries the source platform's redirects into the new project's `config.json` — previously they were only listed in the migration report as manual work. Non-wildcard rules now count as converted.

### Fixed

- Search on configured-`base_url` sites fetched its index from the absolute base URL, so previews, mirrors, and local serves of the built site broke search with a cross-origin error. The index is now fetched relative to the page, working on the canonical domain and any same-origin copy alike.
- The search error message met neither light- nor dark-theme contrast requirements; it is now themed and AA-compliant.

## [v0.6.4] - 2026-07-18

### Navigation

- Wide desktop (≥1200px) pins the site nav open as a persistent left sidebar: no interaction needed, the hamburger hides, and the logo reverts to a plain home link. Below 1200px the toggle behavior is unchanged. Content centers between the left nav and the right table of contents with a 900px reading measure.
- Visible breadcrumb trail on every non-home page — Home › directory groups (named via `_category.json`) or frontmatter category › page title — alongside the existing JSON-LD breadcrumbs.
- The pinned sidebar scrolls the active page into view when it sits below the fold.
- Sidebar groups already auto-collapse to the active branch; now documented behavior.

### Section hub pages

- `_category.json` accepts `"index": true`: the directory gets a generated landing page listing its pages (with frontmatter descriptions) and nested groups. A source `index.md` always wins. Hubs appear in the sitemap, search index, and AI artifacts, gain an **Overview** link in their nav group, and breadcrumb directory crumbs link to them.

### SEO

- `og:url`, `og:image`, and `twitter:image` (plus the card type that depends on the image) are emitted only when absolute, as the OpenGraph spec requires — zero-config builds previously shipped relative values that scrapers ignore. Configured-`base_url` sites are unchanged.
- The post-build audit now resolves same-origin absolute URLs against the local build instead of skipping them as external, closing the blind spot that let a dead reference survive on configured-base sites.

## [v0.6.3] - 2026-07-17

### GitHub-flavored Markdown

- Task lists (`- [ ]` / `- [x]`) render as checkboxes instead of literal brackets; each checkbox is label-wrapped so it carries its item text as an accessible name.
- GitHub alerts (`> [!NOTE]`, `[!TIP]`, `[!IMPORTANT]`, `[!WARNING]`, `[!CAUTION]`) render as styled admonitions; adjacent alert blocks that python-markdown merges into one blockquote are split back apart.
- Bare `http(s)://` and `www.` URLs in prose autolink, with trailing punctuation kept outside the link.
- Search-index text extraction now uses the same Markdown pipeline as page rendering: fence markers, fence language tags, table pipe rows, and task markers no longer leak into search snippets.

### Navigation

- The site nav no longer depends on clicking the logo: an always-present hamburger button toggles it (sites without a favicon previously had no header navigation at all), the logo now toggles instead of only opening, and `aria-expanded` is tracked.
- Categorized sites: the slideout now clones the entire navigation (one list per category plus headings) instead of only the first list, with styled category headings and nested groups.
- The mobile table-of-contents button worked for the first time: it was positioned underneath the fixed header and its click handler was never attached. Now placed below the header and wired up.
- Client-side TOC generation no longer overwrites the build's heading ids, which had recreated duplicate anchors (`#setup` twice) and mangled unicode slugs; the TOC also indexes only content headings, not navigation headings.

### Theming

- Light mode was unreadable in the header: the navbar title and every slideout link were hardcoded white on a background that flips to white. Nav colors are now paired variables.
- Manually toggling the theme now recolors the navbar too — previously it only tracked the OS preference, producing a white navbar on a dark page.

### Accessibility

- Zero axe-core violations across every generated page in both color schemes, enforced in CI by a new `audit_a11y.js` gate (with a negative test, like the existing audit).
- Skip-to-content link; the closed slideout's links no longer occupy the tab order (keyboard users previously tabbed through the entire site nav to reach search); focus moves into the nav on open and back to the toggle on close.
- Landmarks and labels: header/banner, labeled navs, `role=search`, named theme toggle; decorative logo alt.
- WCAG AA contrast: admonition titles, code tokens, footer text, and the light-theme link color; content links are underlined rather than color-only.
- Code blocks are keyboard-scrollable (`tabindex="0"`); `prefers-reduced-motion` collapses all animation.

### PWA and artifacts

- The offline fallback page is now actually precached — the service worker referenced `offline.html` but built its cache list before the file was written, so offline navigation to an uncached URL had always shown the browser error page.
- `noindex` frontmatter is honored by `llms.txt`, `llms-full.txt`, and `skill.md`, matching the search index and sitemap.
- Projects without a root `404.md` get a default styled 404 page; the raw-Markdown alternate (`.html.md`) is written for every page, fixing the dead alternate link on 404 pages.
- Sites without a `repo_url` no longer render an empty GitHub link in the footer.

## [v0.6.2] - 2026-07-17

- GFM strikethrough support: `~~text~~` renders as `<del>` instead of literal tildes.
- Deploys now reach already-open pages: when an updated service worker activates, the page reloads once to pick up the new cache (first installs never reload).

## [v0.6.1] - 2026-07-17

- Fixed search-result links double-prefixing the site base on configured-base sites (clicking a result produced `https://site/https://site/page.html` → 404). Absolute index URLs are now used as-is; relative URLs still get the page-base prefix that nested zero-config pages need.

## [v0.6.0] - 2026-07-17

### Migration importer

- New `wingtip migrate <source> [--output DIR]` command converts a hosted documentation project (`docs.json` / `mint.json` configuration) into a new WingTip project. Strictly read-only: the source is never modified.
- Pages (`.md` and `.mdx`) copy with nested paths preserved in URLs; module `import`/`export` lines are stripped from MDX and JSX components are inventoried per page.
- Navigation groups map to directory `_category.json` files where they align with directories; page order carries over as `order` frontmatter.
- Platform-style absolute internal links (`/guides/intro`) rewrite to portable relative Markdown links.
- Site name, description, brand colors, and favicon carry into `config.json` and `theme.json`.
- Every migration emits `migration-report.md`: an executive summary (pages converted, URLs preserved, groups mapped, manual follow-ups) followed by converted items, manual-work details, and next steps.
- Common MDX components are approximated as Markdown: callouts (`Note`/`Warning`/`Tip`/`Info`/`Check`) become blockquotes, `Step`/`Tab`/`Accordion` become bold labels, `Card` becomes a link, layout wrappers are dropped, and any leaf component with a `src` attribute becomes an image. JSX nesting indentation is removed outside code fences; remaining unknown components are inventoried per page.
- Links in raw `href`/`src` attributes are rewritten alongside Markdown links; resolution tries page-relative then site-root paths, with a case-insensitive fallback that emits the canonical on-disk casing.
- Dynamic link expressions (`href={variable}`) are stubbed to `#` and reported; unresolvable internal links are reported as suspected broken links in the source.
- MDX comments (`{/* ... */}`) are stripped; multi-line JSX/HTML tags are joined before conversion.
- Fixed WingTip's link rewriter stripping the `docs/` prefix from links whose URL space legitimately contains `docs/…`.
- Validated against real public hosted-docs repositories of 46, 249, 315, and 5,387 pages: URLs preserved on every page, and every remaining audit finding is an itemized pre-existing source defect (stale links, OpenAPI-generated pages, platform runtime paths).

### Agent-native artifacts

- Every build now emits `skill.md` alongside `llms.txt`: retrieval instructions for AI agents (whole-corpus file, per-page Markdown alternates, citation guidance). Required by the audit gate.
- `wingtip migrate` writes `AGENTS.md` into the new project: docs-maintenance instructions any coding agent can follow — build, verify, add pages, preserve URLs — so the AI your team already uses maintains the docs, no hosted platform required.
- Migration guide gains a "Serving your migrated site" section covering both topologies (dedicated docs domain and main-domain subpath) with copy-paste nginx, Caddy, Vercel, and Netlify configuration; subpath URL correctness (og:url, canonicals, RSS, sitemap, robots, PWA scope) verified against the demo deployment.

### Package and page-weight diet

- Material Icons converted from TTF to WOFF2 (348KB → 125KB) — every generated site's deploy and service-worker precache shrinks accordingly; browsers only fetch the font when an icon glyph is actually used.
- Removed an unreferenced bundled font (297KB). Package: 810KB → 608KB compressed.

### Audit gate

- The post-build auditor now parses pages instead of regex-scanning raw text: only `href`/`src` attributes on rendered elements are checked, so code samples and the raw-markdown embed no longer produce false positives; custom URL schemes (`cursor:`, `vscode:`, …) are treated as external.
- Link-resolution verdicts are memoized, making large-site audits fast (one filesystem check per unique target instead of pages × links).
- The 5,387-page stress test recorded a scaling finding for the roadmap: per-page full navigation makes total output size quadratic in page count; migration and build times scale linearly.

## [v0.5.0] - 2026-07-17

### Nested content and navigation

- `docs/` is now discovered recursively; nested source paths are preserved in generated URLs (`docs/guides/intro.md` → `guides/intro.html`) so existing site structures survive migration.
- Sidebar navigation renders nested directories as collapsible groups, auto-expanded along the active page's path. `_category.json` (`name`, `order`) names and orders groups; `order`/`nav_order` frontmatter orders pages.
- A `README.md` inside a docs subdirectory maps to that directory's `index.html`.
- Content images under `docs/` map to site-root URLs mirroring the source tree.
- Zero-config builds now emit depth-correct relative URLs for assets, canonicals, search, feeds, and PWA files on nested pages.
- Duplicate output paths are detected, warned about, and skipped.
- Search, sitemap, RSS, llms.txt, concatenated docs, and service-worker precache all include nested pages.

### Packaging and CLI

- Relative README links are absolutized at package-build time (`hatch-fancy-pypi-readme`) so they resolve on the PyPI project page; the repo README stays relative for GitHub and the demo site.
- `wingtip --help` describes recursive docs discovery.

## [v0.4.2] - 2026-07-17

- Fixed the README social-card image on PyPI by using an absolute URL.
- Reworded the branding guarantee: generated sites carry no "powered by" badge, injected links, or generator watermarks.
- Optimized the social card image from 546KB to 244KB.

## [v0.4.1] - 2026-07-17

### Packaging and first-run experience

- Added a standard Python package with `pyproject.toml` and the `wingtip` console command.
- Bundled templates, styles, scripts, fonts, and other runtime assets in the wheel.
- Added `--source`, `--serve`, `--regen-card`, `--output`, and `--version` CLI options.
- Made zero-configuration builds derive project identity from the source repository instead of inheriting WingTip branding.
- Added a cold-install wheel fixture to verify the first-run experience outside the source checkout.

### Search and discovery

- Added per-page title, description, keywords, canonical, robots/noindex, Open Graph, Twitter, author, date, language, category, and version metadata.
- Added `TechArticle` and breadcrumb JSON-LD, RSS, `llms.txt`, concatenated documentation, and per-page Markdown alternates.
- Added hreflang alternates and language-aware page metadata.
- Excluded noindexed pages from search, sitemap, category/version indexes, and structured data.

### Performance, offline use, and security

- Vendored core frontend dependencies so generated sites do not require dependency CDNs.
- Added responsive local-image variants, intrinsic dimensions, and lazy loading.
- Added a PWA manifest, service worker, and offline fallback.
- Made favicon and PWA icon generation opt-in to project-provided branding.
- Added configurable analytics, custom head snippets, and Content Security Policy output.

### Quality and extensibility

- Added plugin hooks before and after conversion/build plus plugin-provided Markdown extensions.
- Added a post-build auditor for missing local files, CDN regressions, required artifacts, PWA consistency, and branding leaks.
- Added a CI negative test proving that the auditor rejects deliberately broken output.
- Fixed Markdown links containing fragments or query strings and removed stale raw-documentation links.

### Documentation

- Repositioned WingTip around portable, SEO-first documentation output.
- Added an honest current-capability roadmap and hosted-platform migration guide.
- Added a structured public migration-review intake form.
- Documented current limitations, including top-level-only content discovery, MDX compatibility, and OpenAPI generation.

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
