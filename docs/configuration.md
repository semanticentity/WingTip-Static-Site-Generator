# Configuration

WingTip uses a `config.json` file in your project root to control metadata, theming, GitHub integration, and social card generation.

This file is **required** if you use:

* A custom favicon
* Social card generation (`--regen-card`)
* SEO-friendly `base_url`, `og_image`, or `twitter_handle`
* GitHub "Edit this page" links

---

## Example `config.json`

```json
{
  "base_url": "https://yourusername.github.io/yourrepo",
  "project_name": "WingTip",
  "version": "0.1.0",
  "description": "SEO-friendly Markdown-to-HTML static site generator for GitHub Pages",
  "author": "Your Name",
  "repo_url": "https://github.com/yourusername/yourrepo/",
  "og_image": "social-card.png",
  "favicon": "https://yourcdn.com/favicon.png",
  "twitter_handle": "@yourhandle",
  "github": {
    "repo": "yourusername/yourrepo",
    "branch": "main"
  },
  "social_card": {
    "title": "WingTip",
    "tagline": "Make your docs fly.",
    "theme": "light",
    "font": "Poppins",
    "image": "social-card.png"
  }
}
```

---

## Top-Level Fields

| Key              | Required | Description                                                   |
| ---------------- | -------- | ------------------------------------------------------------- |
| `base_url`       | ✔︎       | Your GitHub Pages URL (used in canonical links, sitemap, etc) |
| `project_name`   | ✔︎       | Name of your project (shown in nav and footer)                |
| `version`        | ✱        | Optional version string shown in footer                       |
| `description`    | ✔︎       | Used in meta tags, Open Graph, Twitter                        |
| `author`         | ✱        | Used in meta tags                                             |
| `repo_url`       | ✱        | Used in footer GitHub link                                    |
| `og_image`       | ✱        | Open Graph image (used unless generated)                      |
| `favicon`        | ✱        | PNG favicon shown in nav                                      |
| `twitter_handle` | ✱        | Shown in meta tags                                            |

---

## GitHub Integration

| Key             | Required | Description          |
| --------------- | -------- | -------------------- |
| `github.repo`   | ✔︎       | e.g. `username/repo` |
| `github.branch` | ✱        | Defaults to `main`   |

Used to generate **"Edit this page on GitHub"** links.

---

## Social Card Settings

| Key                   | Required | Description           |
| --------------------- | -------- | --------------------- |
| `social_card.title`   | ✔︎       | Large text on card    |
| `social_card.tagline` | ✔︎       | Subtitle text         |
| `social_card.theme`   | ✱        | `"light"` or `"dark"` |
| `social_card.font`    | ✱        | Any Google Font       |
| `social_card.image`   | ✱        | Path to output PNG    |

To generate the card, run:

```bash
python wingtip/main.py --regen-card
```

If no `og_image` is set, the PNG is also copied to `./social-card.png`.

---

## Font Notes

* WingTip uses the Google Fonts API to fetch and cache fonts
* If unavailable, it will fall back to `Arial` or a system font
* Fonts are stored in `wingtip/fonts/` if downloaded

---

## Fallback Behavior

| Scenario              | Behavior                                                                       |
| --------------------- | ------------------------------------------------------------------------------ |
| `config.json` missing | Falls back to hardcoded defaults (but no favicon/social card support)          |
| `og_image` unset      | Falls back to generated `docs/site/social-card.png` and copies to project root |
| `favicon` unset       | Default browser icon will be used                                              |

---

## Advanced Considerations

### Plugins and Sensitive Data

The [plugin system](./plugins.md) allows you to extend WingTip's functionality. If you develop plugins that require sensitive information (e.g., API keys, tokens):
-   **Avoid hardcoding secrets** directly in your plugin files.
-   **Do not store secrets directly in `config.json`** if you commit `config.json` to your repository, as it's often public.
-   Prefer using environment variables or other secure methods to provide secrets to your plugins during the build process, especially in CI/CD environments. WingTip itself does not currently have a dedicated secrets management system that plugins can tap into, so this responsibility lies with the plugin developer and the build environment setup.
