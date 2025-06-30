"""
Sample WingTip Plugin: Banner Plugin

This plugin demonstrates how to use the WingTip plugin system by adding
a customizable banner to the top of each page.
"""

class BannerPlugin:
    """A plugin that adds a banner to the top of each page."""
    
    def __init__(self, config=None):
        """Initialize the plugin with optional configuration."""
        self.config = config or {}
        self.banner_text = config.get('text', 'This is a sample banner added by the banner plugin!')
        self.banner_type = config.get('type', 'info')  # info, warning, or danger
        
    def before_markdown_conversion(self, md_content, metadata, filepath):
        """Hook called before markdown is converted to HTML."""
        # No modifications needed at this stage
        return md_content
        
    def after_html_generation(self, html_content, metadata, filepath):
        """Hook called after markdown is converted to HTML but before page assembly."""
        # Add our banner div after the first heading
        banner_html = f'<div class="banner banner-{self.banner_type}">{self.banner_text}</div>'
        
        # Find the first </h1> tag and insert our banner after it
        h1_end = html_content.find('</h1>')
        if h1_end != -1:
            return html_content[:h1_end + 5] + banner_html + html_content[h1_end + 5:]
        return html_content
        
    def after_full_page_assembly(self, final_html, metadata, output_filepath):
        """Hook called after the full page HTML is assembled."""
        # No modifications needed at this stage
        return final_html

# Required: Plugin class must be named 'Plugin'
Plugin = BannerPlugin
