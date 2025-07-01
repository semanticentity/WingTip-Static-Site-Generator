# Plugin Development Guide

WingTip includes a plugin system that allows you to extend and customize the build process. This guide explains how to create and use plugins.

## Plugin Basics

A WingTip plugin is a Python module that defines a class with specific hook methods. The plugin class can modify content at various stages of the build process.

### Plugin Structure

Here's the basic structure of a plugin:

```python
class MyPlugin:
    def __init__(self, config=None):
        """Initialize plugin with optional configuration."""
        self.config = config or {}
    
    def before_markdown_conversion(self, md_content, metadata, filepath):
        """Called before markdown is converted to HTML."""
        return md_content
        
    def after_html_generation(self, html_content, metadata, filepath):
        """Called after markdown is converted but before page assembly."""
        return html_content
        
    def after_full_page_assembly(self, final_html, metadata, output_filepath):
        """Called after the full page HTML is assembled."""
        return final_html

# Required: Plugin class must be named 'Plugin'
Plugin = MyPlugin
```

### Hook Points

Plugins can hook into three points in the build process:

1. **before_markdown_conversion**: Modify raw markdown before it's converted to HTML
2. **after_html_generation**: Modify generated HTML before it's inserted into the page template
3. **after_full_page_assembly**: Modify the complete HTML page before it's written to disk

## Sample Plugin

WingTip includes a sample banner plugin that demonstrates the plugin system. You can find it in `plugins/sample_banner_plugin.py`:

```python
class BannerPlugin:
    def __init__(self, config=None):
        self.config = config or {}
        self.banner_text = config.get('text', 'This is a sample banner!')
        self.banner_type = config.get('type', 'info')
        
    def after_html_generation(self, html_content, metadata, filepath):
        banner_html = f'<div class="banner banner-{self.banner_type}">{self.banner_text}</div>'
        h1_end = html_content.find('</h1>')
        if h1_end != -1:
            return html_content[:h1_end + 5] + banner_html + html_content[h1_end + 5:]
        return html_content

Plugin = BannerPlugin
```

## Using Plugins

To use a plugin:

1. Place your plugin file in the `plugins/` directory
2. Update your `config.json` to enable and configure the plugin:

```json
{
  "plugins": {
    "banner": {
      "enabled": true,
      "config": {
        "text": "Welcome to my docs!",
        "type": "info"
      }
    }
  }
}
```

## Creating Your Own Plugin

1. Create a new Python file in the `plugins/` directory
2. Define your plugin class with the desired hook methods
3. Assign your class to `Plugin` at the module level
4. Configure the plugin in `config.json`

### Example: Code Stats Plugin

Here's an example plugin that counts lines of code in code blocks:

```python
class CodeStatsPlugin:
    def after_html_generation(self, html_content, metadata, filepath):
        import re
        code_blocks = re.findall(r'<pre><code.*?>(.*?)</code></pre>', 
                               html_content, re.DOTALL)
        total_lines = sum(block.count('\n') + 1 for block in code_blocks)
        stats_html = f'<p class="code-stats">This page contains {total_lines} lines of code.</p>'
        return html_content + stats_html

Plugin = CodeStatsPlugin
```

## Best Practices

1. **Documentation**: Include docstrings and comments explaining your plugin's purpose and configuration options
2. **Error Handling**: Gracefully handle errors and edge cases
3. **Performance**: Keep modifications efficient, especially for large sites
4. **Testing**: Test your plugin with various content types and edge cases

## Plugin API Reference

### Hook Methods

#### before_markdown_conversion
- **Parameters**:
  - `md_content`: Raw markdown content
  - `metadata`: Page metadata from frontmatter
  - `filepath`: Source markdown file path
- **Returns**: Modified markdown content

#### after_html_generation
- **Parameters**:
  - `html_content`: Generated HTML content
  - `metadata`: Page metadata
  - `filepath`: Source file path
- **Returns**: Modified HTML content

#### after_full_page_assembly
- **Parameters**:
  - `final_html`: Complete page HTML
  - `metadata`: Page metadata
  - `output_filepath`: Output file path
- **Returns**: Modified page HTML

### Configuration

Plugins can access their configuration through `self.config` in the plugin class. The configuration is loaded from `config.json`.
