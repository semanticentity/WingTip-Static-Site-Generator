# WingTip Roadmap

## Feature Comparison

| Feature               | WingTip v1                 | MkDocs | Docusaurus | VitePress |
| --------------------- | -------------------------- | ------ | ---------- | --------- |
| **Markdown Support**  | Basic+                     | Good   | Advanced   | Advanced  |
| **Code Highlighting** | Pygments (themed)          | Good   | Advanced   | Advanced  |
| **Dark Mode**         | Auto + toggle              | Basic  | Advanced   | Advanced  |
| **Live Reload**       | Full (w/ scroll restore)   | Good   | Advanced   | Advanced  |
| **Auto Sidebar**      | Yes                        | Yes    | Advanced   | Advanced  |
| **Search**            | Client-side (JSON)         | Basic  | Advanced   | Good      |
| **TOC Navigation**    | Yes                        | Good   | Advanced   | Good      |
| **Prev/Next Links**   | Yes                        | Basic  | Good       | Good      |
| **Social Cards**      | Built-in (Pillow)          | None   | Basic      | None      |
| **SEO**               | Canonical + sitemap + meta | Basic  | Advanced   | Good      |
| **Analytics**         | Not yet                    | Basic  | Advanced   | Good      |
| **Versioning**        | Yes (Basic)                | No     | Yes        | No        |
| **Plugin System**     | Yes (Basic)                | Basic  | Yes        | Yes       |
| **Admonitions**       | Yes                        | Yes    | Yes        | Yes       |
| **Math (KaTeX)**      | Yes                        | No     | Yes        | Yes       |
| **GFM Support**       | Enhanced                   | Good   | Advanced   | Advanced  |


## Recently Added

*   **Full GitHub-Flavored Markdown (GFM) Support:** Enhanced Markdown parsing using `markdown-it-py` including tables, task lists, strikethrough, etc.
*   **LaTeX-style Math Rendering:** Integrated KaTeX for client-side rendering of math expressions.
*   **Document Versioning:** Support for building multiple documentation versions from different source directories, with a UI selector.
*   **Basic Plugin System:** Introduced a plugin architecture with hooks for `before_markdown_conversion`, `after_html_generation`, and `after_full_page_assembly`.
*   **Admonition Blocks:** Support for common admonition types (note, warning, danger, etc.) with CSS styling.
*   **Client-Side Search:** Implemented in v0.3.0 using a local JSON index.

## Planned Features

### Navigation

* Nested sidebar sections (grouping by folder or heading)
* Collapsible sidebar sections
* Keyboard shortcuts for navigation and toggles

### Markdown Enhancements

* Mermaid diagram rendering
* Image captioning syntax

### Developer Experience

* True HMR (hot module reload) without full page refresh
* Build errors shown in browser overlay
* CLI scaffolding (`wingtip new my-docs`)
* Local theme overrides via custom CSS

### SEO & Output Polish

* JSON-LD structured data for articles
* Author/date metadata in frontmatter
* RSS feed generation
* Animated copy-to-clipboard feedback
* Custom 404 page (Basic version implemented, could be enhanced)

### Longer-Term Ideas

* i18n / localization
* Offline mode (PWA shell)
* Advanced plugin features (event bus, more hooks, UI interactions)

## Accessibility

*   Enhanced ARIA attributes for all interactive elements.
*   WCAG 2.1 AA compliance audit and necessary improvements.
*   Keyboard navigation improvements for all UI components.

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
