# Theming in WingTip

WingTip provides a flexible way to customize the appearance of your documentation site. You can start with basic overrides for fonts and colors, and for more advanced needs, standard CSS practices can be employed.

## Basic Theme Overrides (`theme.json`)

The primary way to customize your site's look and feel is by creating a `theme.json` file in the root of your project (the same directory as your `config.json`). This file allows you to define global font choices and specify colors for both light and dark modes.

If `theme.json` is not present, or if specific keys within it are missing, WingTip will use its default styles, which are based on Water.css and predefined font stacks.

### Structure of `theme.json`

The `theme.json` file has three main top-level keys:

*   `"fonts"`: For defining global font families.
*   `"light_mode"`: For defining colors specific to the light theme.
*   `"dark_mode"`: For defining colors specific to the dark theme.

### Example `theme.json`

```json
{
  "fonts": {
    "sans_serif": "\"Inter\", -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, Oxygen, Ubuntu, Cantarell, \"Fira Sans\", \"Droid Sans\", \"Helvetica Neue\", sans-serif",
    "monospace": "\"JetBrains Mono\", Menlo, Monaco, Consolas, \"Liberation Mono\", \"Courier New\", monospace"
  },
  "light_mode": {
    "background_body": "#FCFCFC",
    "background_element": "#FFFFFF",
    "text_main": "#333333",
    "text_bright": "#000000",
    "links_or_primary": "#005FB8",
    "border": "#E0E0E0"
  },
  "dark_mode": {
    "background_body": "#1E1E1E",
    "background_element": "#2C2C2C",
    "text_main": "#E0E0E0",
    "text_bright": "#FFFFFF",
    "links_or_primary": "#3391FF",
    "border": "#4A4A4A"
  }
}
```

### Detailed Configuration

#### 1. Fonts

The `fonts` object accepts two keys:

*   **`sans_serif`**: (String) A CSS `font-family` stack for the main body text.
    *   _Default_: `system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', 'Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji', sans-serif`
    *   _Example_: `"Inter", sans-serif`
*   **`monospace`**: (String) A CSS `font-family` stack for code blocks (`<pre><code>`) and inline code (`<code>`).
    *   _Default_: `Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace`
    *   _Example_: `"Fira Code", monospace`

WingTip will use these values to set the `--theme-font-family-sans-serif` and `--theme-font-family-monospace` CSS variables. The `body` and code elements are styled to use these variables.

#### 2. Light Mode & Dark Mode Colors

The `light_mode` and `dark_mode` objects accept the same set of keys to define colors for their respective themes. All values should be valid CSS color strings (e.g., hex codes like `#RRGGBB`, color names like `blue`, `rgb(...)`, `hsl(...)`).

| Key                  | Corresponding Water.css Variable | Description                                                                              |
| -------------------- | -------------------------------- | ---------------------------------------------------------------------------------------- |
| `background_body`    | `--background-body`              | The main background color of the page.                                                   |
| `background_element` | `--background`                   | Background for elements like inline code, inputs, default buttons, even-numbered table rows. |
| `text_main`          | `--text-main`                    | The primary color for most body text.                                                      |
| `text_bright`        | `--text-bright`                  | Color for headings (`<h1>`-`<h6>`) and bold/strong text.                                    |
| `links_or_primary`   | `--links`                        | Color for hyperlinks. This often serves as the site's primary accent color.              |
| `border`             | `--border`                       | Color for table borders, `<hr>` elements, fieldset borders, etc.                         |
_You can also add other keys if you wish to define additional theme-specific color variables (e.g., `"secondary_accent": "#value"`), which would generate `--theme-color-secondary-accent-light` and `--theme-color-secondary-accent-dark`. These would then need to be used in your own custom CSS._

When you define these color keys, WingTip generates CSS variables that override the default Water.css styles. For example, `light_mode.background_body = "#FAF7F0"` will set the `--background-body` CSS variable to `#FAF7F0` when the light theme is active.

This system allows for quick and easy visual customization of your documentation.

### Tips for Choosing Colors and Fonts

*   **Contrast:** Ensure sufficient contrast between text colors and background colors for readability, especially for accessibility (WCAG AA guidelines are a good reference).
*   **Font Legibility:** Choose fonts that are clear and easy to read for body text and code. Consider fonts designed for UIs or reading.
*   **Consistency:** Try to maintain a consistent feel between your light and dark mode themes, even if colors are inverted.
*   **Test:** Always preview your changes in both light and dark modes to ensure they look as expected.

## Advanced CSS Customization

While `theme.json` provides a straightforward way to change common visual elements, you might have more specific styling needs. For these scenarios, you can:

1.  **Create a `custom.css` file:** Place this file in your `static/css/` directory (e.g., `static/css/custom.css`).
2.  **Link it in `template.html`:** You would need to modify your local `template.html` (if you've ejected or copied it for customization) to include a link to this stylesheet. Make sure to link it *after* the Water.css link and after the injected theme variables style block if you want your custom CSS to override them.

    ```html
    <head>
      ...
      <link id="watercss-theme" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/light.css">
      <style id="custom-theme-variables">
        $custom_theme_styles
      </style>
      <link rel="stylesheet" href="syntax.css">
      <link rel="stylesheet" href="${base_url}/static/css/custom.css"> <!-- Add your custom CSS -->
      ...
    </head>
    ```
    *(Note: The `${base_url}` part is important if your site is not served from the root of a domain).*

This approach gives you full CSS power to target any element and apply any style.

## Future: Theme Plugins

As outlined in the [Roadmap](roadmap.md), we envision a more powerful **Plugin System** for WingTip in the future. A key part of this system would be **Theme Plugins**.

Unlike the `theme.json` file, which is for simple value overrides (fonts, colors), theme plugins would offer much deeper customization capabilities, potentially including:

*   **Custom HTML Templates:** Providing entirely different HTML structures for pages.
*   **Custom JavaScript:** Adding new client-side functionalities or interactions.
*   **Advanced CSS Processing:** Integrating tools like Sass or PostCSS for more complex stylesheets.
*   **New Asset Types:** Managing and including different types of static assets.
*   **Complete Visual Overhauls:** Creating unique themes that go far beyond color and font changes.

This plugin system would provide a structured way for developers to create and share complete themes, transforming the look, feel, and even functionality of a WingTip site. Stay tuned for developments in this area!
