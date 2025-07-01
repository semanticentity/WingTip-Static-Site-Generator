#!/usr/bin/env python3

import os
import re
import sys
import json
import gzip
import pathlib
import hashlib
import argparse
import markdown
import shutil
import html as html_module 
from string import Template
from bs4 import BeautifulSoup 
from datetime import datetime
import yaml 
from latex_extension import LaTeXPreservationExtension

OUTPUT_DIR = "docs/site"

def show_help():
    """
wingtip/main.py - Minimal Markdown to HTML static site generator

USAGE:
  python wingtip/main.py [options]

OPTIONS:
  --output DIR        Output directory (default: docs/site)
  --regen-card        Force regenerate social card

OUTPUT:
  ./README.md          -> ./docs/site/index.html
  ./docs/*.md          -> ./docs/site/*.html
  ./docs/site/index.html    -> generated doc index
  ./sitemap.xml        -> XML sitemap for all .html files

REQUIREMENTS:
  pip install markdown beautifulsoup4

NOTES:
  - Adds top-right Docs link
  - Adds custom favicon support
  - Adds light/dark mode toggle
  - Adds TOC, .md link rewrite, GitHub edit link
  - Adds copy buttons to all code blocks
"""
    print(show_help.__doc__)

# Load config
DEFAULT_CONFIG = {
    "project": "WingTip",
    "tagline": "Clean docs that soar",
    "description": "Minimal static site generator for beautiful documentation. Clean Markdown to HTML conversion with modern features.",
    "author": "SemanticEntity",
    "og_image": "social-card.png",
    "twitter_handle": "",
    "concat_docs_filename": "wingtip.txt",
    "version": "0.4.1",
    "repo_url": "",
}
CFG_PATH = pathlib.Path("config.json")
CONFIG = DEFAULT_CONFIG.copy()
if CFG_PATH.exists():
    CONFIG.update(json.loads(CFG_PATH.read_text()))

THEME_CFG_PATH = pathlib.Path("theme.json")
THEME_CONFIG = {}
if THEME_CFG_PATH.exists():
    try:
        THEME_CONFIG = json.loads(THEME_CFG_PATH.read_text())
    except json.JSONDecodeError as e:
        print(f"Warning: Could not parse theme.json: {e}. Using default theme.")

BASE_URL = CONFIG["base_url"].rstrip("/") or "."

# Load and format template
def load_template():
    path = os.path.join(os.path.dirname(__file__), "template.html")
    raw = pathlib.Path(path).read_text(encoding="utf8")
    return Template(raw)

TEMPLATE = load_template()

DEFAULT_SANS_SERIF_FONT_STACK = "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', 'Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji', sans-serif"
DEFAULT_MONOSPACE_FONT_STACK = "Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace"

def generate_theme_css(theme_config):
    """Generates style tag with theme CSS variables."""
    if not theme_config:  # If no theme config, return empty style tag with comment
        return '<style id="custom-theme-variables">\n    /* No custom theme styles */\n</style>'
    
    css_parts = []
    css_parts.append('<style id="custom-theme-variables">\n    /* Theme overrides */')

    fonts = theme_config.get("fonts", {})
    sans_serif = fonts.get("sans_serif", DEFAULT_SANS_SERIF_FONT_STACK)
    monospace = fonts.get("monospace", DEFAULT_MONOSPACE_FONT_STACK)

    css_parts.append("\n    :root {")
    css_parts.append(f"      --theme-font-family-sans-serif: {sans_serif};")
    css_parts.append(f"      --theme-font-family-monospace: {monospace};")
    css_parts.append("    }")

    # Water.css variable mappings
    water_css_map = {
        "background_body": "--background-body",
        "background_element": "--background",
        "text_main": "--text-main",
        "text_bright": "--text-bright",
        "links_or_primary": "--links",
        "border": "--border",
        "nav_background": "--nav-background",
        "bg_admonition": "--bg-admonition",
        "admonition_note_bg": "--admonition-note-bg",
        "admonition_note_text": "--admonition-note-text",
        "admonition_warning_bg": "--admonition-warning-bg",
        "admonition_warning_text": "--admonition-warning-text",
        "admonition_danger_bg": "--admonition-danger-bg",
        "admonition_danger_text": "--admonition-danger-text",
        "admonition_tip_bg": "--admonition-tip-bg",
        "admonition_tip_text": "--admonition-tip-text",
        "admonition_info_bg": "--admonition-info-bg",
        "admonition_info_text": "--admonition-info-text",
        "admonition_success_bg": "--admonition-success-bg",
        "admonition_success_text": "--admonition-success-text",
        "admonition_note_border": "--admonition-note-border",
        "admonition_warning_border": "--admonition-warning-border",
        "admonition_danger_border": "--admonition-danger-border",
        "admonition_tip_border": "--admonition-tip-border",
        "admonition_info_border": "--admonition-info-border",
        "admonition_success_border": "--admonition-success-border",
        # Add more mappings if needed, e.g. for --button-base, --code, etc.
    }

    if "light_mode" in theme_config:
        css_parts.append("\n    html.light:root, :root[data-theme='light'] {") # Target both JS class and potential data-attribute
        for key, value in theme_config["light_mode"].items():
            if key in water_css_map:
                css_parts.append(f"      {water_css_map[key]}: {value};")
            # Allow defining other --theme-color-*-light variables as well
            css_parts.append(f"      --theme-color-{key.replace('_', '-')}-light: {value};")
        css_parts.append("    }")

    if "dark_mode" in theme_config:
        css_parts.append("\n    html.dark:root, :root[data-theme='dark'] {") # Target both JS class and potential data-attribute
        for key, value in theme_config["dark_mode"].items():
            if key in water_css_map:
                css_parts.append(f"      {water_css_map[key]}: {value};")
            css_parts.append(f"      --theme-color-{key.replace('_', '-')}-dark: {value};")
        css_parts.append("    }")

    css_parts.append("\n</style>")
    return "\n".join(css_parts)

# Helper to build canonical URLs
def make_url(rel_path):
    rel_path = rel_path.lstrip("/")
    if rel_path == "index.html":
        rel_path = ""
    return f"{BASE_URL}/{rel_path}".rstrip("/")

def write_robots_txt():
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /search_index.json"
    ]

    # Determine Sitemap URL
    # Ensure base_url is taken from CONFIG and handled if it's '.' or missing
    base_url_for_sitemap = CONFIG.get("base_url", "").rstrip('/')
    if base_url_for_sitemap and base_url_for_sitemap != '.':
        lines.append(f"Sitemap: {base_url_for_sitemap}/sitemap.xml")
    else:
        # For local preview (base_url = '.') or missing base_url, use a root-relative path
        lines.append(f"Sitemap: /sitemap.xml")

    with open(os.path.join(OUTPUT_DIR, "robots.txt"), "w", encoding="utf8") as f:
        f.write("\n".join(lines) + "\n") # Add trailing newline

def write_sitemap_xml(pages):
    with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), "w", encoding="utf8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for path in pages:
            rel_path = path.replace(OUTPUT_DIR + "/", "").lstrip("/")
            f.write(f'  <url><loc>{BASE_URL}/{rel_path}</loc></url>\n')
        f.write('</urlset>\n')

def generate_syntax_css():
    """Generate syntax highlighting CSS for both light and dark modes"""
    from pygments.formatters import HtmlFormatter
    from pygments.styles import get_style_by_name
    
    # Dark theme (monokai)
    dark_formatter = HtmlFormatter(style='monokai')
    dark_css = dark_formatter.get_style_defs('pre code')
    
    # Light theme - Set 1: Modern IDEs
    light_themes = ['vs', 'xcode', 'solarized-light', 'gruvbox-light']
    light_css = ''
    for theme in light_themes:
        try:
            formatter = HtmlFormatter(style=theme)
            css = formatter.get_style_defs('pre code')
            light_css += f'/* {theme} */\n{css}\n\n'
        except Exception as e:
            print(f"Warning: Could not generate {theme} theme: {e}")
    
    # Write combined CSS with media queries
    css_content = f'''
/* Dark mode (default) */
:root:not([data-theme="light"]) pre code {{
{dark_css}
}}

/* Light mode */
:root[data-theme="light"] pre code,
@media (prefers-color-scheme: light) {{
  pre code {{
    background: #f8f8f8;
    {light_css}
  }}
}}
'''
    
    css_path = os.path.join(OUTPUT_DIR, 'syntax.css')
    with open(css_path, 'w') as f:
        f.write(css_content)

def copy_static_files():
    """Copy static files to output directory"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generate syntax highlighting CSS
    generate_syntax_css()
    
    # Handle favicon
    favicon_dest = os.path.join(OUTPUT_DIR, "favicon.png")
    if CONFIG.get("favicon"):
        try:
            import urllib.request
            urllib.request.urlretrieve(CONFIG["favicon"], favicon_dest)
        except Exception as e:
            print(f"Warning: Failed to download favicon: {e}")

    # Copy the entire 'static' directory if it exists
    static_src_dir = "static"
    if os.path.isdir(static_src_dir): # Source must be a directory
        static_dest_dir = os.path.join(OUTPUT_DIR, "static")

        # Handle existing destination: remove if it's a file or a directory
        if os.path.exists(static_dest_dir):
            if os.path.isdir(static_dest_dir):
                shutil.rmtree(static_dest_dir)
            else:
                os.remove(static_dest_dir) # Remove if it's a file

        try:
            shutil.copytree(static_src_dir, static_dest_dir)
            print(f"Copied static assets from '{static_src_dir}' to '{static_dest_dir}'")
        except FileNotFoundError:
             print(f"Warning: Source static directory '{static_src_dir}' not found. Skipping copy.")
        except Exception as e:
            print(f"Warning: Could not copy static assets from '{static_src_dir}': {e}")


def extract_title(md):
    match = re.search(r"^# (.+)", md, re.MULTILINE)
    return match.group(1).strip() if match else "Untitled"

def add_codeblock_copy_buttons(html):
    soup = BeautifulSoup(html, "html.parser")
    for i, code in enumerate(soup.select("pre > code")):
        # Normalize class="language-xyz" to class="xyz"
        classes = code.get("class", [])
        for j, cls in enumerate(classes):
            if cls.startswith("language-"):
                classes[j] = cls.replace("language-", "")
        if not classes:
            classes = ["plaintext"]
        code["class"] = classes

        # Add copy button
        btn = soup.new_tag("button", type="button")
        btn.string = "📌"
        btn["class"] = "copy-btn"
        btn["style"] = "float:right;margin-bottom:0.5em;display:inline-block;font-size:0.8em;padding:10px;position:absolute;right:-15px;top:-10px;"
        btn["data-code-id"] = f"codeblock-{i+1}"
        code["id"] = f"codeblock-{i+1}"
        code.parent.insert_before(btn)

    # Inject copy script if needed
    if not soup.find_all("script", string=lambda s: s and "copy-btn" in s):
        script = soup.new_tag("script")
        script.string = '''
        document.querySelectorAll('.copy-btn').forEach(function(btn){
          btn.addEventListener('click', function(){
            var codeId = btn.getAttribute('data-code-id');
            var codeElem = document.getElementById(codeId);
            if (codeElem) {
              var text = codeElem.innerText;
              if (navigator.clipboard) {
                navigator.clipboard.writeText(text);
              } else {
                var textarea = document.createElement('textarea');
                textarea.value = text;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
              }
              btn.innerText = 'Copied!';
              setTimeout(function(){ btn.innerText = '📌'; }, 1200);
            }
          });
        });
        '''
        soup.body.append(script) if soup.body else soup.append(script)

    return str(soup)



def build_navigation(current_file: str) -> str:
    """Build the navigation section HTML."""
    nav_html = ['<div class="navigation">']  
    nav_html.append('<h2>Documentation</h2>')
    nav_html.append('<ul>')
    
    # Add link to README/index
    nav_html.append('<li><a href="index.html">README</a></li>')
    
    # Add links to all docs
    docs_dir = "docs"
    if os.path.isdir(docs_dir):
        for name in sorted(os.listdir(docs_dir)):
            if name.endswith('.md'):
                base = os.path.splitext(name)[0]
                nav_html.append(f'<li><a href="{base}.html">{base.title()}</a></li>')
    
    nav_html.append('</ul>')
    nav_html.append('</div>')
    return '\n'.join(nav_html)

def get_prev_next_links(current_file: str) -> tuple[str, str]:
    """Get the previous and next page links for navigation."""
    docs_dir = os.path.join(os.path.dirname(__file__), 'docs')
    if not os.path.exists(docs_dir):
        return '', ''

    # Get all markdown files
    md_files = sorted([f for f in os.listdir(docs_dir) if f.endswith('.md')])
    
    # Find current index
    try:
        current_index = md_files.index(os.path.basename(current_file))
    except ValueError:
        return '', ''

    # Get prev/next files
    prev_file = md_files[current_index - 1] if current_index > 0 else ''
    next_file = md_files[current_index + 1] if current_index < len(md_files) - 1 else ''

    # Build links
    prev_link = f'<a href="{prev_file.replace(".md", ".html")}" class="prev">← {prev_file.replace(".md", "").title()}</a>' if prev_file else ''
    next_link = f'<a href="{next_file.replace(".md", ".html")}" class="next">{next_file.replace(".md", "").title()} →</a>' if next_file else ''

    return prev_link, next_link

def add_codeblock_copy_buttons(html: str) -> str:
    """Add copy buttons to code blocks."""
    soup = BeautifulSoup(html, 'html.parser')
    for i, code in enumerate(soup.select('pre > code')):
        # Normalize class="language-xyz" to class="xyz"
        classes = code.get('class', [])
        if classes:
            lang_class = next((c for c in classes if c.startswith('language-')), None)
            if lang_class:
                code['class'] = lang_class[9:]
        
        # Add copy button
        button = soup.new_tag('button', 
                            **{'class': 'copy-btn', 
                               'data-clipboard-target': f'#code-{i}',
                               'title': 'Copy to clipboard'})
        button.string = 'Copy'
        
        # Add wrapper div
        wrapper = soup.new_tag('div', **{'class': 'code-wrapper'})
        code.parent.wrap(wrapper)
        wrapper.insert(0, button)
        
        # Add ID to code block
        code['id'] = f'code-{i}'
    
    return str(soup)

def remove_frontmatter(md_text):
    """Removes frontmatter from markdown text."""
    if md_text.startswith("---"):
        parts = md_text.split("---", 2)
        if len(parts) > 2:
            return parts[2].strip()
    return md_text

def generate_search_index(pages_data, output_dir):
    """Generates search_index.json from pages data."""
    search_index = []
    for page_item in pages_data:
        title = page_item["title"]
        content_md = page_item["content_md"]
        url = page_item["url"]

        # Convert markdown to HTML
        html_content = markdown.markdown(content_md)

        # Strip HTML tags to get plain text
        soup = BeautifulSoup(html_content, "html.parser")
        text_content = soup.get_text(separator=' ').strip()

        # Ensure URL is absolute by prepending base_url if needed
        if not url.startswith(('http://', 'https://', '/')):
            url = f"{BASE_URL}/{url}"

        search_index.append({
            "title": title,
            "text": text_content,
            "url": url
        })

    output_path = os.path.join(output_dir, "search_index.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf8") as f:
        json.dump(search_index, f, indent=2)
    print(f"Generated search index: {output_path}")

def convert_markdown_file(input_path, output_filename, add_edit_link=False, prev_page=None, next_page=None):
    with open(input_path, "r", encoding="utf8") as f:
        md = f.read()
    
    # Check for YAML front matter
    front_matter = {}
    if md.startswith('---'):
        try:
            # Find the second '---' to extract front matter
            end_marker = md.find('---', 3)
            if end_marker != -1:
                front_matter_text = md[3:end_marker].strip()
                front_matter = yaml.safe_load(front_matter_text) or {}
                # Remove front matter from markdown content
                md = md[end_marker + 3:].strip()
        except Exception as e:
            print(f"Warning: Error parsing front matter: {e}")

    # Create a custom link pattern processor
    class LinkRewriter(markdown.treeprocessors.Treeprocessor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Load external link config
            self.config = self.load_config()

        def load_config(self):
            """Load external link configuration from config.json"""
            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
                return config.get('external_links', {
                    'open_in_new_tab': True,
                    'exclude_domains': [],
                    'include_domains': [],
                    'exclude_paths': [],
                    'attributes': {
                        'rel': 'noopener noreferrer',
                        'class': 'external-link'
                    }
                })
            except Exception as e:
                print(f"Warning: Could not load external link config: {e}")
                return {}

        def is_external_link(self, href):
            """Check if a URL is external (starts with http:// or https://)"""
            return href and href.startswith(('http://', 'https://'))

        def should_open_in_new_tab(self, href):
            """Determine if a link should open in a new tab based on config rules"""
            if not self.is_external_link(href):
                return False

            # Extract domain from href
            from urllib.parse import urlparse
            domain = urlparse(href).netloc

            # Check exclude_domains
            if any(domain.endswith(d) for d in self.config.get('exclude_domains', [])):
                return False

            # Check include_domains
            if any(domain.endswith(d) for d in self.config.get('include_domains', [])):
                return True

            # Check exclude_paths
            path = urlparse(href).path
            if any(fnmatch.fnmatch(path, pattern) for pattern in self.config.get('exclude_paths', [])):
                return False

            # Use global setting
            return self.config.get('open_in_new_tab', True)

        def run(self, root):
            for element in root.iter('a'):
                href = element.get('href')
                if not href:
                    continue

                if self.is_external_link(href):
                    # Handle external link according to config
                    if self.should_open_in_new_tab(href):
                        element.set('target', '_blank')
                        # Add additional attributes from config
                        for key, value in self.config.get('attributes', {}).items():
                            element.set(key, value)
                else:
                    # Handle internal link rewriting
                    if href.startswith(('#', '/')):
                        continue

                    # Handle .md extension conversion
                    if href.endswith('.md'):
                        href = href[:-3] + '.html'

                    # Handle docs/ prefix for local development vs GitHub Pages
                    if href.startswith('docs/'):
                        href = href[5:]  # Remove docs/ prefix
                    elif not any(href.startswith(prefix) for prefix in ['index.html', 'assets/', 'static/', 'images/']):
                        # For files that aren't in special directories and don't start with docs/
                        # we need to ensure they're relative to the current file
                        href = href

                    element.set('href', href)
            return root
    
    class LinkRewriterExtension(markdown.Extension):
        def extendMarkdown(self, md):
            md.treeprocessors.register(LinkRewriter(md), 'link_rewriter', 7)
    
    # Convert markdown to HTML with link rewriting and GFM features
    html = markdown.markdown(
        md,
        extensions=[
            "fenced_code",
            "codehilite", 
            "tables",
            "nl2br",           # Newlines to <br>
            "sane_lists",     # Better list handling
            "smarty",         # Smart quotes, dashes, etc
            "attr_list",     # {: .class} style attributes
            "def_list",      # Definition lists
            "footnotes",     # [^1] style footnotes
            "md_in_html",    # Markdown inside HTML
            "toc",           # [TOC] generation
            "admonition",    # !!! note style admonitions
            LinkRewriterExtension(),
            "latex_extension"
        ],
        extension_configs={
            'admonition': {
                'nested_content': True
            }
        },
        output_format="html5"
    )
    
    # Replace LaTeX placeholders with actual delimiters
    html = html.replace('DISPLAYMATH_START', '\\[')
    html = html.replace('DISPLAYMATH_END', '\\]')
    html = html.replace('INLINEMATH_START', '\\(')
    html = html.replace('INLINEMATH_END', '\\)')

    # Add copy buttons to code blocks
    html = add_codeblock_copy_buttons(html)

    # Wrap all tables in a responsive div
    soup = BeautifulSoup(html, 'html.parser')
    for table in soup.find_all('table'):
        wrapper = soup.new_tag('div', attrs={'class': 'table-responsive'})
        table.insert_before(wrapper)
        wrapper.append(table)
    # Serialize soup back to HTML for further processing
    html = str(soup)

    h1 = soup.find('h1')
    title = h1.text if h1 else os.path.basename(input_path)

    # Get navigation links
    nav_links = build_navigation(input_path)

    # Build prev/next links
    prev_link = f'<a href="{prev_page[1]}" class="prev">← {prev_page[0]}</a>' if prev_page else ''
    next_link = f'<a href="{next_page[1]}" class="next">{next_page[0]} →</a>' if next_page else ''

    # Add edit on GitHub link if requested
    if add_edit_link and CONFIG.get("github", {}).get("repo"):
        repo = CONFIG["github"]["repo"]
        branch = CONFIG["github"].get("branch", "main")
        path = os.path.relpath(input_path)
        edit_url = f"https://github.com/{repo}/edit/{branch}/{path}"
        html += f'\n<p class="edit-link"><a href="{edit_url}">Edit this page on GitHub</a></p>'

    # Get page URL
    page_url = make_url(os.path.basename(output_filename))

    # Build page using global template
    # Handle favicon URL - if base_url is '.', use relative path
    favicon_url = 'favicon.png' if BASE_URL == '.' else f'{BASE_URL}/favicon.png'

    # Construct URL for the concatenated docs file
    concat_docs_filename = CONFIG.get("concat_docs_filename", "concatenated_docs.txt")
    # For local development (BASE_URL is '.'), use a relative path
    if BASE_URL == '.':
        concat_docs_url = concat_docs_filename
    else:
        concat_docs_url = f"{BASE_URL}/{concat_docs_filename}"

    # Determine raw markdown content to pass to template
    raw_markdown_for_template = ""
    if add_edit_link: # Only try to read if it's a page that would have source
        try:
            with open(input_path, 'r', encoding='utf8') as f:
                raw_markdown_for_template = f.read()
        except Exception as e:
            print(f"Warning: Could not read raw markdown from {input_path}: {e}")

    # Generate custom theme CSS
    custom_theme_variables_style = generate_theme_css(THEME_CONFIG)

    page = TEMPLATE.substitute(
        title=title,
        canonical_url=page_url,
        page_url=page_url,
        content=html,
        project=CONFIG["project_name"],
        description=CONFIG["description"],
        author=CONFIG["author"],
        og_image=CONFIG["og_image"],
        twitter_handle=CONFIG["twitter_handle"],
        version=CONFIG["version"],
        year=datetime.now().year,
        repo_url=CONFIG["repo_url"],
        navigation=nav_links,
        prev_link=prev_link,
        next_link=next_link,
        base_url=BASE_URL,
        favicon_url=favicon_url,
        concat_docs_url=concat_docs_url,
        raw_markdown_content=raw_markdown_for_template,
        custom_theme_variables_style=custom_theme_variables_style
    )

    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    with open(output_filename, "w", encoding="utf8") as f:
        f.write(page)

def get_page_nav(pages, current_index):
    """Get previous and next page links"""
    prev_page = pages[current_index - 1] if current_index > 0 else None
    next_page = pages[current_index + 1] if current_index < len(pages) - 1 else None
    return prev_page, next_page

def generate_concatenated_markdown():
    """Generates a single Markdown file from README.md and docs/*.md (excluding 404.md)."""
    all_markdown_content = []
    files_to_process = []

    # Add README.md if it exists
    if os.path.exists("README.md"):
        files_to_process.append("README.md")

    # Add files from docs/ directory, excluding 404.md
    docs_dir = "docs"
    if os.path.isdir(docs_dir):
        for name in sorted(os.listdir(docs_dir)):
            if name.endswith(".md") and name != "404.md":
                files_to_process.append(os.path.join(docs_dir, name))

    for filepath in files_to_process:
        try:
            with open(filepath, "r", encoding="utf8") as f:
                content = f.read()
            all_markdown_content.append(f"\n---\nFile: {filepath}\n---\n\n{content}")
        except Exception as e:
            print(f"Warning: Could not read or process file {filepath}: {e}")

    if not all_markdown_content:
        print("No Markdown files found to concatenate.")
        return

    concatenated_content = "".join(all_markdown_content)

    output_filename = CONFIG.get("concat_docs_filename", "concatenated_docs.txt")
    full_output_path = os.path.join(OUTPUT_DIR, output_filename)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    try:
        with open(full_output_path, "w", encoding="utf8") as f:
            f.write(concatenated_content)
        print(f"Generated concatenated docs: {full_output_path}")
    except Exception as e:
        print(f"Error writing concatenated Markdown file: {e}")

def cleanup_output_dir(generated_files):
    """Remove files in OUTPUT_DIR that are not in the list of generated files.
    Only removes .html files to avoid touching assets, images, etc."""
    for root, _, files in os.walk(OUTPUT_DIR):
        for file in files:
            if file.endswith('.html'):
                full_path = os.path.join(root, file)
                if full_path not in generated_files:
                    print(f"Removing obsolete file: {full_path}")
                    os.remove(full_path)

def main():
    parser = argparse.ArgumentParser(description=show_help.__doc__ or "Minimal Markdown to HTML static site generator")
    parser.add_argument("--regen-card", action="store_true", help="Force regenerate social card")
    parser.add_argument("--output", help="Output directory (default: docs/site)")
    parser.add_argument("--serve", action="store_true", help="Start dev server after build")
    args = parser.parse_args()
    
    # Update output dir if specified
    global OUTPUT_DIR
    if args.output:
        OUTPUT_DIR = args.output

    copy_static_files()
    generate_concatenated_markdown() # Call the new function here
    pages = []
    search_data_for_index = []
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    social = CONFIG.get("social_card", {})
    card_path = pathlib.Path(OUTPUT_DIR) / "social-card.png"
    should_generate = args.regen_card or not social.get("image") or not card_path.exists()

    if should_generate:
        try:
            from wingtip.generate_card import generate_social_card
        except ImportError:
            # For direct script execution
            from generate_card import generate_social_card
        generate_social_card(
            social.get("title", CONFIG["project"]),
            social.get("tagline", "Make your docs fly."),
            theme=social.get("theme", "light"),
            font=social.get("font", "Poppins")
        )

    if not CONFIG["og_image"]:
        CONFIG["og_image"] = f'{BASE_URL}/social-card.png'
        # Copy social-card.png to root if it was generated
        if card_path.exists():
            import shutil
            root_card = pathlib.Path("social-card.png")
            shutil.copy2(card_path, root_card)

    # First collect all doc files and their titles
    docs_dir = "docs"
    nav_pages = []
    
    # Start with README if it exists
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf8") as f:
            readme_content_raw = f.read()
        readme_title = extract_title(readme_content_raw)
        readme_md_content_no_frontmatter = remove_frontmatter(readme_content_raw)
        search_data_for_index.append({
            "title": readme_title,
            "content_md": readme_md_content_no_frontmatter,
            "url": "index.html"
        })
        nav_pages.append((readme_title, "index.html", "README.md"))
    
    # Then collect all .md files from docs directory
    if os.path.isdir(docs_dir):
        for name in os.listdir(docs_dir):
            if name.endswith(".md"):
                md_path = os.path.join(docs_dir, name)
                with open(md_path, "r", encoding="utf8") as f:
                    md_content_raw = f.read()
                title = extract_title(md_content_raw)

                if name != "404.md":
                    md_content_no_frontmatter = remove_frontmatter(md_content_raw)
                    html_filename = f"{os.path.splitext(name)[0]}.html"
                    search_data_for_index.append({
                        "title": title,
                        "content_md": md_content_no_frontmatter,
                        "url": html_filename
                    })
                base = os.path.splitext(name)[0]
                nav_pages.append((title, f"{base}.html", md_path))
    
    # Convert all files with prev/next navigation
    for i, (title, html_file, md_path) in enumerate(nav_pages):
        prev_page = nav_pages[i-1][:2] if i > 0 else None
        next_page = nav_pages[i+1][:2] if i < len(nav_pages)-1 else None
        
        output_path = os.path.join(OUTPUT_DIR, html_file)
        convert_markdown_file(md_path, output_path, add_edit_link=True,
                            prev_page=prev_page, next_page=next_page)
        pages.append(f"{OUTPUT_DIR}/{html_file}")

    # Process 404.md if it exists
    fourofour_md_path = pathlib.Path("404.md")
    if fourofour_md_path.exists():
        fourofour_html_path = pathlib.Path(OUTPUT_DIR) / "404.html"
        # Title will be extracted by convert_markdown_file from H1 or default to filename
        convert_markdown_file(
            input_path=str(fourofour_md_path),
            output_filename=str(fourofour_html_path),
            add_edit_link=False,  # Typically no "edit this page" for a 404
            prev_page=None,
            next_page=None
        )
        pages.append(str(fourofour_html_path))
        
        # For GitHub Pages compatibility, also copy 404.html to the root of the site
        # This ensures it works with the permalink: /404.html front matter

    generate_search_index(search_data_for_index, OUTPUT_DIR)
    write_sitemap_xml(pages)
    write_robots_txt()
    
    # Clean up obsolete files
    cleanup_output_dir(pages)
    
    # Start dev server if requested
    if args.serve:
        import subprocess
        import sys
        import time
        from pathlib import Path
        
        serve_script = Path(__file__).parent / "serve.py"
        kill_script = Path(__file__).parent / "killDocs.sh"
        
        if serve_script.exists():
            print("\nStarting development server...")
            try:
                # First attempt to start the server
                result = subprocess.run([sys.executable, str(serve_script)], capture_output=True, text=True)
                if result.returncode != 0 and "Address already in use" in result.stderr:
                    print("Port 8000 is in use. Attempting to free it...")
                    if kill_script.exists():
                        # Try to kill existing processes using killDocs.sh
                        try:
                            subprocess.run(["./killDocs.sh"], check=True, cwd=str(kill_script.parent))
                            print("Successfully freed port 8000. Retrying server start...")
                            time.sleep(1)  # Give the system a moment
                            # Try starting the server again
                            subprocess.run([sys.executable, str(serve_script)], check=True)
                        except subprocess.CalledProcessError as e:
                            print(f"Failed to free port: {e}")
                            sys.exit(1)
                    else:
                        print("./killDocs.sh not found. Please free port 8000 manually.")
                        sys.exit(1)
                elif result.returncode != 0:
                    print(f"\nServer failed to start: {result.stderr}")
                    sys.exit(1)
            except KeyboardInterrupt:
                print("\nServer stopped by user")

if __name__ == "__main__":
    main()
