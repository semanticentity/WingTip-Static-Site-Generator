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

## Basic Theme Overrides (`theme.json`)

WingTip allows you to customize the basic look and feel of your documentation site, such as fonts and key colors for both light and dark modes, by creating a `theme.json` file in the root of your project (alongside `config.json`).

If `theme.json` is not present, or if specific keys are missing, the site will use the default styles provided by Water.css and WingTip's predefined font stacks.

### Example `theme.json`

```json
{
  "fonts": {
    "sans_serif": "\"Open Sans\", Arial, sans-serif",
    "monospace": "\"Fira Code\", Consolas, monospace"
  },
  "light_mode": {
    "background_body": "#FAF7F0",
    "background_element": "#FFFFFF",
    "text_main": "#3C3C3C",
    "text_bright": "#1E1E1E",
    "links_or_primary": "#007ACC",
    "border": "#DCDCDC"
  },
  "dark_mode": {
    "background_body": "#1C1C1E",
    "background_element": "#2A2A2C",
    "text_main": "#EAEAEA",
    "text_bright": "#FFFFFF",
    "links_or_primary": "#58A6FF",
    "border": "#3A3A3C"
  }
}
```

### Configuration Structure

*   **`fonts`**:
    *   `sans_serif`: (String) CSS `font-family` stack for the main body text. Defaults to a system UI font stack.
    *   `monospace`: (String) CSS `font-family` stack for code blocks and inline code. Defaults to a common monospace font stack.
*   **`light_mode`**: An object containing color overrides for the light theme.
*   **`dark_mode`**: An object containing color overrides for the dark theme.

### Color Keys for `light_mode` and `dark_mode`

The following keys can be used within `light_mode` and `dark_mode` to customize colors. All values should be valid CSS color strings (e.g., hex codes like `#RRGGBB`, color names like `blue`, `rgb()`, `hsl()`).

| Key                  | Corresponding Water.css Variable (for reference) | Description                                                                 |
| -------------------- | ------------------------------------------------ | --------------------------------------------------------------------------- |
| `background_body`    | `--background-body`                              | The main background color of the page.                                      |
| `background_element` | `--background`                                   | Background for elements like code snippets, inputs, default buttons, etc. |
| `text_main`          | `--text-main`                                    | The primary color for body text.                                            |
| `text_bright`        | `--text-bright`                                  | Color for headings and strong text.                                         |
| `links_or_primary`   | `--links`                                        | Color for hyperlinks and can act as a primary accent color.                 |
| `border`             | `--border`                                       | Color for borders on tables, fieldsets, hr elements, etc.                 |

When you define these keys in your `theme.json`, WingTip will generate CSS variables that override the default Water.css styles. For example, specifying `light_mode.background_body` will override the `--background-body` variable when the light theme is active.

This provides a simple way to quickly brand your documentation site. For more advanced CSS customizations, you can still use a custom CSS file linked in your `template.html` or add inline styles.
