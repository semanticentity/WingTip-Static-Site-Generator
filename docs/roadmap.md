# WingTip Roadmap

## Feature Comparison

| Feature                       | WingTip v1                                       | MkDocs | Docusaurus | VitePress | Mintlify |
| ----------------------------- | ------------------------------------------------ | ------ | ---------- | --------- | -------- |
| **Markdown Support**          | Advanced (GFM + extras)                          | Good   | Advanced   | Advanced  | Advanced |
| **Code Highlighting**         | Pygments (themed)                                | Good   | Advanced   | Advanced  | Advanced |
| **Dark Mode**                 | Auto + toggle + CSS vars                         | Basic  | Advanced   | Advanced  | Advanced |
| **Live Reload**               | Full (w/ scroll restore)                         | Good   | Advanced   | Advanced  | Advanced |
| **Auto Sidebar**              | Yes                                              | Yes    | Advanced   | Advanced  | Advanced |
| **Search**                    | Client-side (JSON)                               | Basic  | Advanced   | Good      | Advanced |
| **TOC Navigation**            | Yes + keyboard shortcuts                         | Good   | Advanced   | Good      | Good     |
| **Prev/Next Links**           | Yes                                              | Basic  | Good       | Good      | Good     |
| **Social Cards**              | Built-in (Pillow)                                | None   | Basic      | None      | Built-in |
| **SEO (frontmatter overrides)** | Advanced (per-page title, canonical, noindex, OG/Twitter, keywords) | Basic  | Advanced   | Good      | Advanced |
| **Theme System**              | CSS vars + JSON config                           | Basic  | Advanced   | Good      | Advanced |
| **External Links**            | Configurable + new tab                           | Basic  | Basic      | Basic     | Basic    |
| **Math Support**              | KaTeX                                            | Plugin | MDX        | Plugin    | Good     |
| **Admonitions**               | Yes (Material style)                             | Plugin | MDX        | Plugin    | Yes      |
| **Analytics**                 | Not yet                                          | Basic  | Advanced   | Good      | Built-in |
| **Versioning**                | Not yet                                          | No     | Yes        | No        | Yes      |

## Planned Features

### Navigation

* Nested sidebar sections (grouping by folder or heading)
* ~~Search with local JSON index~~ (Implemented in v0.3.0)
* Collapsible sidebar sections
* ~~Keyboard shortcuts for navigation and toggles~~ (Implemented in v0.4.0)

### Markdown Enhancements

* ~~Basic admonition support~~ (Implemented in v0.4.1)
* Advanced admonition features:
  * Support for nested content (lists, code blocks)
  * Basic icon support via Material Icons
  * Theme-aware styling with CSS variables
  * Future enhancements (deferred):
    * Support for pymdownx.admonition extension
    * Custom icons via FontAwesome
    * Nested admonitions
    * Custom admonition types
    * Collapsible admonitions
    * Icon customization per theme
    * Support for tables inside list items (Python-Markdown limitation)
* Mermaid diagram rendering
* ~~LaTeX/math support via KaTeX~~ (Implemented in v0.4.0)
* Image captioning syntax

### Developer Experience

* True HMR (hot module reload) without full page refresh
* Build errors shown in browser overlay
* CLI scaffolding (`wingtip new my-docs`)
* ~~Local theme overrides via custom CSS~~ (Basic theming via `theme.json` implemented in v0.4.0 - [Learn more](theming.md))
* ~~Combined build and serve command~~ (Implemented in v0.4.1 via `--serve` flag)
* ~~Smart port handling for dev server~~ (Implemented in v0.4.1 with auto-retry and port cleanup)
* Automatic cleanup of obsolete files (deferred to future release)

### SEO & Output Polish

* ~~JSON-LD structured data for articles~~ (Implemented in v0.4.0)
* ~~Per-page SEO frontmatter overrides (title, description, keywords, canonical, noindex, Open Graph, Twitter cards)~~ (Implemented in v0.5.0)
* ~~Author/date metadata in frontmatter~~ (Implemented in v0.5.0)
* ~~RSS feed generation~~ (Implemented in v0.5.0)
* Animated copy-to-clipboard feedback
* ~~Custom 404 page~~ (Implemented in v0.4.1)

### Performance, Security, & Extensibility

* ~~Image lazy loading and intrinsic size attributes for local images~~ (Implemented in v0.5.0)
* ~~Analytics / custom `<head>` snippet hook~~ (Implemented in v0.5.0)
* ~~Default Content Security Policy meta tag~~ (Implemented in v0.5.0)
* Responsive `srcset` image generation

### Longer-Term Ideas

* Documentation Versioning & Categories
  * **Category Support:**
    * Auto-generate categories from docs/ subfolders
    * Category metadata via _category.json (name, description, icon, order)
    * Category-based navigation and breadcrumbs
    * Category-specific themes and templates
    * Category-based search filtering
    * Cross-category linking and references
  * **Versioning Options:**
    * File-level versioning (most granular, complex navigation)
    * Category-level versioning (logical grouping, easier navigation)
    * Repository-level versioning (simple but all-or-nothing)
    * Version aliases (latest, stable, dev)
    * Version-aware navigation and search
    * Cross-version linking support
* i18n / localization
* ~~Offline mode (PWA shell)~~ (Implemented in v0.5.0)
* Plugin system (before/after hooks, Markdown extensions, theme plugins)
    * *Theme plugins could allow for entirely new site structures, custom JavaScript, advanced CSS processing (Sass, PostCSS), and template overrides, offering a much deeper level of customization than `theme.json`.*

## Future: Theme Plugins

We envision a more powerful **Plugin System** for WingTip in the future. A key part of this system would be **Theme Plugins**.

Unlike the `theme.json` file, which is for simple value overrides (fonts, colors), theme plugins would offer much deeper customization capabilities, potentially including:

*   **Custom HTML Templates:** Providing entirely different HTML structures for pages.
*   **Custom JavaScript:** Adding new client-side functionalities or interactions.
*   **Advanced CSS Processing:** Integrating tools like Sass or PostCSS for more complex stylesheets.
*   **New Asset Types:** Managing and including different types of static assets.
*   **Complete Visual Overhauls:** Creating unique themes that go far beyond color and font changes.

This plugin system would provide a structured way for developers to create and share complete themes, transforming the look, feel, and even functionality of a WingTip site. 

## Accessibility

* ~~Enhanced ARIA attributes for interactive elements~~ (Implemented in v0.4.0)
* WCAG 2.1 AA compliance audit and necessary improvements
* ~~Keyboard navigation improvements~~ (Implemented in v0.4.0 for search, more to come)

## Performance Optimization

*   Advanced asset optimization (e.g., image compression, code splitting).
*   Lazy loading for images and other offscreen content.
*   Performance budget and monitoring.

## Security Considerations

*   Implement Content Security Policy (CSP) by default.
*   Regular dependency audits and updates for security vulnerabilities.
*   Guidance on securing user-generated content if applicable.

## Community & Contribution

*   Detailed `CONTRIBUTING.md` guide.
*   Automated PR checks for linting and tests.
*   Consider a "Good first issue" program for new contributors.

## Deployment

*   Guides for deploying to popular platforms (e.g., GitHub Pages, Netlify, Vercel).
*   CLI command or integration for easier deployment.
