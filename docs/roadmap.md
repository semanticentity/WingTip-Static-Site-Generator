# WingTip Roadmap

## Objective

Make WingTip the easiest credible exit from a hosted documentation platform: migrate an existing repository, preserve its information architecture and URLs, generate portable static output, and prove the result with automated search, performance, and integrity audits.

WingTip will not try to reproduce every hosted collaboration feature. It will compete on ownership, migration quality, technical discovery, build transparency, portability, and zero mandatory platform cost.

## Current position

Status reflects the repository as of July 16, 2026. Competitor capabilities change; any public comparison must be generated from a reproducible fixture rather than unsupported marketing claims.

| Capability | WingTip now | Competitive status | Priority |
| --- | --- | --- | --- |
| Portable static HTML output | Yes | Leadership target | Maintain |
| No mandatory hosted runtime | Yes | Leadership target | Maintain |
| No mandatory CDN frontend assets | Yes | Leadership target | Maintain |
| No imposed generator branding | Yes | Leadership target | Maintain |
| Canonical, robots, sitemap, RSS, OG/Twitter | Yes | Strong parity | Maintain |
| `TechArticle` and breadcrumb JSON-LD | Yes | Strong parity | Expand validation |
| `llms.txt`, full docs, Markdown alternates | Yes | Strong parity | Add agent skills |
| Per-page noindex, dates, language, category, version | Yes | Strong parity | Improve UI |
| Hreflang alternates | Yes | Search differentiator | Add cluster audit |
| Local search | Yes | Basic parity | Ranking controls |
| PWA and offline fallback | Yes | Differentiator | Maintain |
| Responsive image generation | Yes | Differentiator | Add budgets |
| Configurable analytics, head snippets, and CSP | Yes | Strong parity | Validate policies |
| Plugin hooks and Markdown extensions | Yes | Extensibility base | Formalize API |
| Post-build integrity/branding audit | Yes | Leadership target | Expand |
| Recursive content trees | No | Parity blocker | P0 |
| Grouped, nested, tabbed navigation | No | Parity blocker | P0 |
| Redirect migration and static-host outputs | No | Migration blocker | P0 |
| Hosted-platform configuration import | No | Acquisition blocker | P0 |
| MDX compatibility analysis | No | Migration blocker | P0 |
| OpenAPI reference generation | No | Major parity blocker | P1 |
| API playground | No | Major parity blocker | P1 |
| Agent `skill.md` discovery | No | Emerging parity gap | P1 |
| Preview deployments and visual review | No | Workflow gap | P2 |
| Authentication and private docs | No | Enterprise gap | P3/partner |
| Hosted collaborative editor | No | Intentionally not core | Ecosystem |

## Delivery plan

### Phase 0 — Capture the switching window

Ship the acquisition surface before broad feature work:

- ~~Publish an open-source hosted-platform migration guide~~ (Implemented July 17, 2026)
- ~~Offer migration concierge intake through a dedicated GitHub issue template~~ (Implemented July 17, 2026)
- Create a sanitized real-world hosted-platform fixture for regression testing
- Record a repository-to-deployed-site migration demo
- Document output ownership, supported hosts, and unsupported constructs plainly
- Do not use founder controversy in product copy; meet newly receptive users with a concrete exit path

**Exit criteria:** A hosted-platform user can submit a repository and receive a repeatable migration report rather than an informal promise.

### Phase 1 — Migration wedge (P0)

#### Content and navigation model

- ✅ Recursively discover `.md` content (`.mdx` compatibility still pending)
- ✅ Preserve nested source paths in generated URLs (`docs/guides/intro.md` → `guides/intro.html`)
- ✅ Ordered navigation groups: `_category.json` (`name`, `order`) per directory, `order`/`nav_order` frontmatter per page
- ✅ Render grouped/collapsible navigation from the directory tree
- ✅ Detect duplicate output paths (collisions are warned and skipped)
- Introduce tabs, products, versions, and languages in the navigation model
- Render breadcrumb navigation in the page body (JSON-LD breadcrumbs already ship)
- Detect orphaned navigation entries

#### Hosted-platform importer

```bash
wingtip migrate ./existing-docs --output ./wingtip-docs
```

Shipped (read-only — the source project is never modified):

- ✅ Read current and legacy platform configuration formats (`docs.json`, `mint.json`)
- ✅ Import project name, description, brand colors, and favicon
- ✅ Convert navigation groups to directory `_category.json` files and per-page `order` frontmatter
- ✅ Preserve page paths in generated URLs; report every preserved URL
- ✅ Rewrite platform-style absolute internal links to portable relative links
- ✅ Inventory MDX components per page; strip module `import`/`export` lines and MDX comments
- ✅ Approximate common MDX components (callouts → blockquotes, titled sections → labels, `Card` → link, `src`-bearing components → images) with JSX dedenting
- ✅ Rewrite links in raw `href`/`src` attributes with page-relative → site-root → case-insensitive resolution
- ✅ Stub dynamic link expressions and report suspected broken links in the source
- ✅ Report redirects for host-level configuration
- ✅ Never silently discard unsupported configuration or content — everything unhandled is listed in the report
- ✅ Validated against real public hosted-docs repositories (46 → 5,387 pages)

Still pending:

- Resolve local JSON `$ref` configuration
- Convert tabs, products, versions, and languages beyond flat group mapping
- Emit static redirect pages plus host-specific `_redirects` files
- Preserve OpenAPI references for Phase 2 endpoint rendering

#### Migration report

- ✅ Every migration emits `migration-report.md` in the new project: an executive summary (format detected, pages converted, URLs preserved, groups mapped, manual follow-up count) followed by ✓ converted items and ⚠ manual work (components per page, unmapped groups, orphan pages, redirects, configuration not carried) and next steps

Still pending:

- Machine-readable JSON report alongside the Markdown
- Broken links and missing assets detection at migrate time (the post-build audit covers this after `wingtip` runs)
- File/line locations for component occurrences

**Exit criteria:** Representative hosted-platform repositories build without lost pages, URLs, metadata, or unreported incompatibilities.

### Phase 2 — Documentation parity (P1)

Prioritize capabilities that block real migrations:

- OpenAPI 3.x ingestion and endpoint-page generation
- API operation navigation, parameter/schema tables, examples, and code samples
- Optional static-first API playground enhancement
- AsyncAPI inventory and design
- Search weighting/boost frontmatter and section-level result anchors
- Visible version, product, and language switchers
- Redirect validation and redirect-chain detection
- Mermaid diagrams
- Common hosted-platform MDX compatibility components: cards, columns, tabs, accordions, steps, callouts, frames, and code groups
- Reusable snippets/includes and content variables
- Navigation banners, badges, deprecation labels, and hidden-page controls
- Formal, versioned plugin API and template/theme extension points

**Exit criteria:** A typical public SaaS documentation repository does not need to remain on a hosted documentation platform solely for navigation, common MDX presentation, or OpenAPI reference pages.

### Phase 3 — Search-engineering leadership (P1)

Turn the existing auditor into a differentiated discovery system:

- Validate titles, descriptions, canonicals, robots directives, OG/Twitter metadata, and JSON-LD
- Detect canonical conflicts, duplicate metadata, orphan pages, broken fragments, redirect chains, and accidental noindex
- Validate hreflang reciprocity, language codes, canonicals, and `x-default` clusters
- Audit internal-link depth and surface pages with weak contextual connectivity
- Add configurable HTML, CSS, JavaScript, image, request-count, and font performance budgets
- Emit machine-readable audit output for CI annotations
- Generate a crawl graph and diff it between builds
- Add optional answer-first/content-structure linting without making ranking promises
- Generate `skill.md`, multiple skill manifests, integrity hashes, and well-known discovery endpoints from project-owned source files
- Add schema types appropriate to API references, software applications, organizations, and FAQs only when content qualifies

**Exit criteria:** WingTip catches technical discovery regressions before deployment and produces evidence that can be inspected in CI.

### Phase 4 — Reproducible competitive benchmark (P1)

Build the same public fixture with WingTip and representative hosted and open-source documentation generators. Record:

- Build inputs, product versions, commands, and generated artifacts
- HTML availability without client-side JavaScript
- Page weight, requests, external origins, and JavaScript execution
- Lighthouse and Core Web Vitals lab results under identical conditions
- Canonical, robots, sitemap, hreflang, social metadata, structured data, and AI-readable artifacts
- Broken-link, accessibility, and schema validation results
- Hosting portability and platform-dependent behavior

Publish raw outputs and rerunnable automation. Do not claim leadership where the fixture does not prove it.

**Exit criteria:** Competitive claims in the README and launch material are generated from public evidence.

### Phase 5 — Workflow and ecosystem (P2)

- `wingtip new`, `wingtip check`, and `wingtip migrate` command groups
- Browser build-error overlay and improved incremental rebuilds
- Preview-deployment recipes for GitHub, Netlify, Cloudflare Pages, and Vercel
- PR annotations for audit regressions and visual changes
- Theme packages and template overrides
- WCAG 2.2 AA audit and regression checks
- Contributor guide, extension examples, and stable fixtures
- Dependency, package-integrity, and generated-CSP checks

### Phase 6 — Optional hosted capabilities (P3)

Keep the open-source generator complete on its own. Hosted or partner services may later provide:

- Managed builds and previews
- Password-protected or authenticated documentation
- Team editing and approval workflows
- Search/feedback analytics
- Edge redirects, headers, and cache controls
- Enterprise support and migration services

These services must not make existing static generation, SEO metadata, auditing, or output ownership dependent on a WingTip account.

## Success metrics

- Migration completion rate and median manual fixes per repository
- Percentage of source pages, URLs, redirects, and metadata preserved
- Unsupported MDX constructs per migrated repository
- Zero unreported data loss
- Audit findings caught before production
- Generated page weight and external-origin count
- Build time across small, medium, and large fixtures
- Number of independent deployments that do not use WingTip-managed infrastructure
- Search impressions, indexed pages, and AI referrals measured by adopters who opt to share results

## Explicit non-goals

- Guaranteed rankings, rich results, or AI citations
- A proprietary content repository
- Mandatory cloud hosting
- Recreating every collaborative editor feature before migration quality is excellent
- Generating large volumes of low-quality programmatic content
- Using competitor controversies as product marketing
