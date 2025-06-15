# Plugin System

WingTip features a basic plugin system that allows you to extend and customize its functionality by writing your own Python code. Plugins can hook into various stages of the site generation process to modify content or perform custom actions.

## Architecture

-   **`plugins/` Directory:** Custom plugins are Python files (`.py`) placed in a directory named `plugins/` at the root of your project.
-   **Loading:** At startup, `main.py` automatically scans the `plugins/` directory for any `*.py` files (excluding `__init__.py`). Each valid Python file found is loaded as a plugin module using `importlib`.
-   **Hooks:** Plugins define their behavior by implementing specific functions called "hooks." If a loaded plugin module has a function with a recognized hook name, WingTip will call it at the appropriate point during the build process.

## Available Hooks

Here are the currently available hooks, listed in the order they are generally executed for each page:

### 1. `before_markdown_conversion(md_content, metadata, filepath)`

-   **Called:** After the raw Markdown content of a file is read and its YAML frontmatter (metadata) has been parsed, but *before* the Markdown content is converted to HTML.
-   **Arguments:**
    -   `md_content` (str): The raw Markdown content of the page (after frontmatter removal).
    -   `metadata` (dict): A dictionary containing the key-value pairs from the page's YAML frontmatter.
    -   `filepath` (str): The absolute path to the source Markdown file.
-   **Return Value:**
    -   A tuple `(modified_md_content, modified_metadata)`. Your plugin **must** return both, even if one is unchanged.
-   **Use Cases:**
    -   Modifying Markdown content programmatically before rendering (e.g., adding generated sections, replacing tokens).
    -   Reading or modifying page metadata which can then be used by other plugins or during HTML templating.
    -   Injecting default metadata values.

### 2. `after_html_generation(html_content, metadata, filepath)`

-   **Called:** After the Markdown content has been converted to HTML (by `markdown-it-py`) and syntax highlighting (by Pygments) has been applied to code blocks. This hook operates on the HTML *body* content, not the full page template.
-   **Arguments:**
    -   `html_content` (str): The generated HTML content for the main body of the page.
    -   `metadata` (dict): The (potentially modified by `before_markdown_conversion`) metadata for the page.
    -   `filepath` (str): The absolute path to the source Markdown file.
-   **Return Value:**
    -   A string containing the (potentially modified) `html_content`.
-   **Use Cases:**
    -   Modifying the raw HTML output from Markdown conversion (e.g., adding specific classes to elements, wrapping sections, parsing and transforming custom HTML structures).
    -   Performing operations on the HTML that require it to be mostly structured but not yet part of the full page layout.

### 3. `after_full_page_assembly(final_html, metadata, output_filepath)`

-   **Called:** After the generated HTML body content has been inserted into the main site template (`template.html`) and the complete, final HTML page string has been assembled.
-   **Arguments:**
    -   `final_html` (str): The complete HTML string for the page, ready to be written to disk.
    -   `metadata` (dict): The metadata for the page.
    -   `output_filepath` (str): The absolute path where the final HTML file will be written.
-   **Return Value:**
    -   A string containing the (potentially modified) `final_html`.
-   **Use Cases:**
    -   Making final modifications to the entire HTML page (e.g., adding banners, injecting scripts or styles in specific locations like `<head>` or end of `<body>`).
    -   Analyzing the final HTML output.
    -   Performing operations that require the full DOM structure of the page.

## Writing a Plugin

A plugin is a simple Python file (e.g., `my_custom_plugin.py`) placed in the `plugins/` directory. You don't need to register it explicitly; WingTip will automatically discover and load it.

To use a hook, define a function in your plugin file with the exact name and signature of one of the available hooks.

**Example Plugin Structure (`plugins/example_plugin.py`):**

```python
# plugins/example_plugin.py

# You can import other modules if needed
# import re

def before_markdown_conversion(md_content, metadata, filepath):
    print(f"[Plugin Example] Processing (before MD): {filepath}")

    # Example: Add a prefix to all pages if not already present
    if not md_content.startswith("## Prefixed! "):
        md_content = f"## Prefixed! \n\n{md_content}"

    # Example: Add a default tag if none are present in metadata
    if "tags" not in metadata:
        metadata["tags"] = ["default_tag"]

    return md_content, metadata

def after_html_generation(html_content, metadata, filepath):
    print(f"[Plugin Example] Processing (after HTML gen): {filepath}")

    # Example: Replace a placeholder in the HTML
    placeholder = "<!-- MY_PLUGIN_PLACEHOLDER -->"
    if placeholder in html_content:
        replacement_text = metadata.get("my_plugin_text", "Default replacement from plugin.")
        html_content = html_content.replace(placeholder, f"<p><strong>Plugin says:</strong> {replacement_text}</p>")

    return html_content

def after_full_page_assembly(final_html, metadata, output_filepath):
    print(f"[Plugin Example] Processing (after full page): {output_filepath}")

    # Example: Add a comment to the end of the HTML
    final_html += "\n<!-- Page processed by example_plugin.py -->"

    return final_html

```

### Important Notes:

-   **Return Values:** Ensure your hook functions return the expected type (e.g., modified content string, or tuple for `before_markdown_conversion`). If a hook doesn't intend to modify the content, it should return the original content it received.
-   **Error Handling:** Errors within a plugin hook will currently propagate and may halt the build process. Wrap your plugin code in `try...except` blocks if you need more robust error handling within the plugin itself.
-   **Metadata:**
    -   The `metadata` dictionary passed to hooks is derived from the YAML frontmatter of each Markdown page.
    -   The `before_markdown_conversion` hook is the only one that can effectively modify metadata for subsequent hooks or for use in the HTML template, as it returns the `modified_metadata`.
-   **Order of Execution:** If multiple plugins implement the same hook, their execution order is determined by the alphabetical order of their filenames within the `plugins/` directory.

## Sample Plugin: `sample_banner_plugin.py`

WingTip includes a sample plugin, `plugins/sample_banner_plugin.py`, which demonstrates the `after_full_page_assembly` hook to add a "Beta Preview" banner to the top of every generated page. It also includes example implementations (commented out or conditional) for the other hooks. Review this file for a practical example.
```
