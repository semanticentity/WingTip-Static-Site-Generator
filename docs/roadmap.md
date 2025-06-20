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
| **Versioning**        | Not yet                    | No     | Yes        | No        |

## Planned Features

### Navigation

* Nested sidebar sections (grouping by folder or heading)
* ~~Search with local JSON index~~ (Implemented in v0.3.0)
* Collapsible sidebar sections
* Keyboard shortcuts for navigation and toggles

### Markdown Enhancements

* Admonition support (`:::note`, etc.)
* Mermaid diagram rendering
* LaTeX/math support via KaTeX
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
* Custom 404 page

### Longer-Term Ideas

* Versioned documentation support
* i18n / localization
* Offline mode (PWA shell)
* Plugin system (before/after hooks, Markdown extensions)

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
