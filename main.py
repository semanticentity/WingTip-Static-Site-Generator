#!/usr/bin/env python3

import os
import re
import sys
import json
import gzip
import pathlib
import hashlib
import argparse
import shutil
import html as html_module
from string import Template
from bs4 import BeautifulSoup
from datetime import datetime
import yaml
from markdown_it import MarkdownIt
from mdit_py_plugins.tasklists import tasklists_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.strikethrough import strikethrough_plugin
from mdit_py_plugins.table import table_plugin
from mdit_py_plugins.admon import admon_plugin # Import for admonitions
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
import importlib.util

# Global variables that will be set by CLI args
INPUT_DIR = "docs"
OUTPUT_DIR = "docs/site"
VERSION_STRING = None
ALL_VERSIONS = []


def show_help():
    """
wingtip/main.py - Minimal Markdown to HTML static site generator

USAGE:
  python wingtip/main.py [options]

OPTIONS:
  --input_dir DIR     Input directory for Markdown files (default: docs)
  --output_dir DIR    Output directory for HTML files (default: docs/site)
  --version_string STR Version string (e.g., v1.0.0)
  --all_versions_json JSON_STR JSON string of all available versions (e.g., '["v1.0", "v0.9"]')
  --regen-card        Force regenerate social card

OUTPUT:
  ./{input_dir}/README.md    -> ./{output_dir}/{version_string}/index.html
  ./{input_dir}/*.md          -> ./{output_dir}/{version_string}/*.html
  ./{output_dir}/{version_string}/index.html -> generated doc index
  ./{output_dir}/{version_string}/sitemap.xml -> XML sitemap for .html files in this version

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
    "version": "0.1.0",
    "repo_url": "",
}
CFG_PATH = pathlib.Path("config.json")
CONFIG = DEFAULT_CONFIG.copy()
if CFG_PATH.exists():
    CONFIG.update(json.loads(CFG_PATH.read_text()))

BASE_URL = CONFIG["base_url"].rstrip("/") or "."

# Load and format template
def load_template():
    path = os.path.join(os.path.dirname(__file__), "template.html")
    raw = pathlib.Path(path).read_text(encoding="utf8")
    return Template(raw)

TEMPLATE = load_template()

# Plugin System
LOADED_PLUGINS = []

def load_plugins():
    """Loads plugins from the 'plugins' directory."""
    global LOADED_PLUGINS
    plugin_dir = pathlib.Path("plugins")
    if not plugin_dir.is_dir():
        print("Plugins directory 'plugins/' not found. Skipping plugin loading.")
        LOADED_PLUGINS = []
        return

    loaded_count = 0
    for plugin_file in plugin_dir.glob("*.py"):
        if plugin_file.name == "__init__.py":
            continue
        try:
            spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                LOADED_PLUGINS.append(mod)
                print(f"Successfully loaded plugin: {plugin_file.name}")
                loaded_count += 1
            else:
                print(f"Warning: Could not create spec for plugin {plugin_file.name}")
        except Exception as e:
            print(f"Warning: Failed to load plugin {plugin_file.name}: {e}")

    if loaded_count > 0:
        print(f"Loaded {loaded_count} plugin(s).")
    else:
        print("No plugins loaded.")

# Helper to build canonical URLs
def make_url(rel_path, version_aware=True):
    rel_path = rel_path.lstrip("/")
    if rel_path == "index.html":
        rel_path = ""

    # Use a temporary base_url from CONFIG, defaulting to "." if not set
    # This avoids issues if BASE_URL global hasn't been updated with version yet
    temp_base_url = CONFIG.get("base_url", ".").rstrip("/")

    if version_aware and VERSION_STRING:
        return f"{temp_base_url}/{VERSION_STRING}/{rel_path}".rstrip("/")
    return f"{temp_base_url}/{rel_path}".rstrip("/")

def write_robots_txt(output_dir_to_use): # Takes specific output_dir
    # Robots.txt is usually global, so it should ideally be in the root of the site,
    # not per version. This function might need to be called differently or only
    # when building the "root" or "latest" version.
    # For now, let's assume it's placed in the root of the *overall* site,
    # which might be the parent of a versioned output directory.
    # Or, if each version is a completely separate site, then it's fine per version.
    # Given the sitemap path, it seems like it's per version.

    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /search_index.json" # This might need to be versioned too
    ]

    base_url_for_sitemap = CONFIG.get("base_url", "").rstrip('/')
    sitemap_path = "sitemap.xml"
    if VERSION_STRING:
        sitemap_path = f"{VERSION_STRING}/sitemap.xml"

    if base_url_for_sitemap and base_url_for_sitemap != '.':
        lines.append(f"Sitemap: {base_url_for_sitemap}/{sitemap_path}")
    else:
        lines.append(f"Sitemap: /{sitemap_path}") # Root-relative

    # Place robots.txt in the root of the current version's output
    # If a global robots.txt is desired, this needs adjustment.
    # For now, it's written into the current version's output_dir.
    # If output_dir_to_use is docs/site/v1.0, robots.txt will be docs/site/v1.0/robots.txt
    # This is probably not what we want for a global robots.txt.
    # Let's assume for now this function is only called for a "root" build,
    # or that each versioned output_dir also gets its own robots.txt pointing to its own sitemap.
    # The latter seems more consistent with sitemap_path logic.

    # If version_string is present, robots.txt should ideally be one level up if it's a global one.
    # For this task, let's assume robots.txt is generated for each version within its dir.
    # This means if you access example.com/v1.0/robots.txt, it will point to example.com/v1.0/sitemap.xml

    robots_path = os.path.join(output_dir_to_use, "robots.txt")
    os.makedirs(os.path.dirname(robots_path), exist_ok=True)
    with open(robots_path, "w", encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")

def write_sitemap_xml(pages, output_dir_to_use, current_version_string):
    sitemap_path = os.path.join(output_dir_to_use, "sitemap.xml")
    os.makedirs(os.path.dirname(sitemap_path), exist_ok=True)

    with open(sitemap_path, "w", encoding="utf8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for page_path_abs in pages:
            # page_path_abs is like /path/to/output_dir/v1.0/page.html
            # We need rel_path to be page.html or sub/page.html relative to version dir
            rel_path = os.path.relpath(page_path_abs, output_dir_to_use).lstrip("./")

            # Construct location URL using make_url for consistency
            # make_url needs the path relative to the version root (or site root if no version)
            loc_url = make_url(rel_path, version_aware=(current_version_string is not None))
            f.write(f'  <url><loc>{loc_url}</loc></url>\n')
        f.write('</urlset>\n')

def generate_syntax_css(output_dir_to_use):
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
    
    css_path = os.path.join(output_dir_to_use, 'syntax.css')
    os.makedirs(os.path.dirname(css_path), exist_ok=True)
    with open(css_path, 'w') as f:
        f.write(css_content)

def copy_static_files(output_dir_to_use, input_dir_to_use): # Added input_dir for clarity, though not directly used for 'static'
    """Copy static files to output directory"""
    os.makedirs(output_dir_to_use, exist_ok=True)
    
    # Generate syntax highlighting CSS into the correct output directory
    generate_syntax_css(output_dir_to_use)
    
    # Handle favicon
    favicon_dest = os.path.join(output_dir_to_use, "favicon.png")
    if CONFIG.get("favicon"):
        try:
            import urllib.request
            urllib.request.urlretrieve(CONFIG["favicon"], favicon_dest)
        except Exception as e:
            print(f"Warning: Failed to download favicon: {e}")

    # Copy the entire 'static' directory if it exists (from project root to output_dir/static)
    # This assumes 'static' is always in the project root, not inside input_dir_to_use.
    project_root_static_dir = "static"
    if os.path.isdir(project_root_static_dir):
        static_dest_dir_abs = os.path.join(output_dir_to_use, "static")

        if os.path.exists(static_dest_dir_abs):
            if os.path.isdir(static_dest_dir_abs):
                shutil.rmtree(static_dest_dir_abs)
            else:
                os.remove(static_dest_dir_abs)

        try:
            shutil.copytree(project_root_static_dir, static_dest_dir_abs)
            print(f"Copied static assets from '{project_root_static_dir}' to '{static_dest_dir_abs}'")
        except FileNotFoundError:
            print(f"Warning: Source static directory '{project_root_static_dir}' not found. Skipping copy.")
        except Exception as e:
            print(f"Warning: Could not copy static assets from '{project_root_static_dir}': {e}")

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



def build_navigation(current_file_abs_path: str, input_dir_to_use: str, current_version_str: str, all_versions_list: list) -> str:
    """Build the navigation section HTML."""
    nav_html = ['<div class="navigation">']
    nav_html.append('<h2>Documentation</h2>')
    nav_html.append('<ul>')

    # Link to current version's README/index, assuming it's at the root of the version
    # The href should be relative to the current page, or an absolute path from site root.
    # If current_file is /output/v1/foo.html, index is /output/v1/index.html
    # A relative link from foo.html to index.html would be "index.html" if in same dir,
    # or "../index.html" if foo.html is in a subdir.
    # For simplicity, let's use root-relative paths for navigation links.
    
    # Base path for links within the current version (e.g., /v1.0 or /)
    version_base_path = ""
    if current_version_str:
        version_base_path = f"/{current_version_str}"

    nav_html.append(f'<li><a href="{version_base_path}/index.html">README</a></li>')

    # Add links to all docs within the current input_dir_to_use
    if os.path.isdir(input_dir_to_use):
        for name in sorted(os.listdir(input_dir_to_use)):
            if name.endswith('.md') and name != "README.md": # README already added
                base = os.path.splitext(name)[0]
                # Nav link should point to /version_string/base.html or /base.html
                nav_html.append(f'<li><a href="{version_base_path}/{base}.html">{base.title()}</a></li>')

    nav_html.append('</ul>')
    nav_html.append('</div>')
    return '\n'.join(nav_html)


def get_prev_next_links(current_file_rel_path: str, input_dir_to_use: str, current_version_str: str) -> tuple[str, str]:
    """Get the previous and next page links for navigation.
    current_file_rel_path is relative to input_dir_to_use (e.g., 'mypage.md' or 'subdir/mypage.md')
    """
    if not os.path.isdir(input_dir_to_use):
        return '', ''

    md_files = []
    for root, _, files in os.walk(input_dir_to_use):
        for file in sorted(files):
            if file.endswith('.md'):
                # Store path relative to input_dir_to_use
                md_files.append(os.path.relpath(os.path.join(root, file), input_dir_to_use))
    
    # Ensure consistent sorting, especially for README.md (often treated as index)
    # README.md or index.md should ideally be first.
    # A simple sort might not be enough if README.md is not first alphabetically.
    # For now, relying on sorted list of relative paths.
    # A common pattern is to have README.md/index.md as the first item.
    # Let's ensure 'README.md' (if exists) is first.
    if "README.md" in md_files:
        md_files.pop(md_files.index("README.md"))
        md_files.insert(0, "README.md")
    elif "index.md" in md_files: # Alternative for index
        md_files.pop(md_files.index("index.md"))
        md_files.insert(0, "index.md")

    if not current_file_rel_path in md_files:
        # This can happen for 404.md if it's outside the main docs dir, or if path is wrong
        print(f"Warning: Current file {current_file_rel_path} not found in discovered md_files for prev/next links.")
        return '', ''

    current_index = md_files.index(current_file_rel_path)
    prev_file_rel_path = md_files[current_index - 1] if current_index > 0 else None
    next_file_rel_path = md_files[current_index + 1] if current_index < len(md_files) - 1 else None

    version_base_path = ""
    if current_version_str: # Ensure version is part of the link
        version_base_path = f"/{current_version_str}"

    prev_link = ''
    if prev_file_rel_path:
        html_path = prev_file_rel_path.replace(".md", ".html")
        title = os.path.splitext(os.path.basename(prev_file_rel_path))[0].title()
        # Links should be root-relative from the site base + version
        prev_link = f'<a href="{CONFIG.get("base_url", ".")}{version_base_path}/{html_path}" class="prev">← {title}</a>'

    next_link = ''
    if next_file_rel_path:
        html_path = next_file_rel_path.replace(".md", ".html")
        title = os.path.splitext(os.path.basename(next_file_rel_path))[0].title()
        next_link = f'<a href="{CONFIG.get("base_url", ".")}{version_base_path}/{html_path}" class="next">{title} →</a>'

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
        content_md = page_item["content_md"] # This is raw markdown
        # url here is relative to the version root, e.g. "mypage.html" or "subdir/mypage.html"
        url = page_item["url"]

        # Convert markdown to HTML using MarkdownIt for consistency
        # Ensure all necessary plugins are included if their output affects search text.
        # For plain text extraction, basic GFM should be enough.
        md_converter_for_search = MarkdownIt("gfm-like").use(table_plugin) # Footnotes might not be critical for search text
        html_content = md_converter_for_search.render(content_md)

        # Strip HTML tags to get plain text
        soup = BeautifulSoup(html_content, "html.parser")
        text_content = soup.get_text(separator=' ').strip()

        # The URL in search_index.json should be relative to the version root
        # E.g., "my-page.html" or "category/my-other-page.html"
        # This way, search.js can construct the full URL using current version or site base.
        search_index.append({
            "title": title,
            "text": text_content,
            "url": url # Already relative to version root
        })

    # output_dir here is the version-specific output directory (e.g., docs/site/v1.0)
    output_path = os.path.join(output_dir, "search_index.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True) # Ensure dir exists
    with open(output_path, "w", encoding="utf8") as f:
        json.dump(search_index, f, indent=2)
    print(f"Generated search index: {output_path}")


def convert_markdown_file(input_path_abs, output_filename_abs, current_version_str, all_versions_list, add_edit_link=False, prev_page_tuple=None, next_page_tuple=None, input_dir_for_file_discovery="docs"):
    # input_path_abs: Absolute path to the source MD file
    # output_filename_abs: Absolute path for the target HTML file
    # current_version_str: e.g., "v1.0" or None
    # all_versions_list: e.g., ["v1.0", "v0.9"]
    # input_dir_for_file_discovery: base input directory for relative path calculations (e.g. docs/v1.0)

    with open(input_path_abs, "r", encoding="utf8") as f:
        md_content_raw = f.read()

    # Check for YAML front matter (metadata)
    metadata = {}
    if md_content_raw.startswith('---'):
        try:
            end_marker = md_content_raw.find('---', 3)
            if end_marker != -1:
                front_matter_text = md_content_raw[3:end_marker].strip()
                metadata = yaml.safe_load(front_matter_text) or {}
                md_content_for_conversion = md_content_raw[end_marker + 3:].strip()
            else: # No closing '---', so no valid frontmatter
                md_content_for_conversion = md_content_raw
                metadata = {}
        except Exception as e:
            print(f"Warning: Error parsing front matter in {input_path_abs}: {e}")
            md_content_for_conversion = md_content_raw
            metadata = {}
    else:
        md_content_for_conversion = md_content_raw
        metadata = {}

    # Hook: before_markdown_conversion
    for plugin in LOADED_PLUGINS:
        if hasattr(plugin, "before_markdown_conversion"):
            try:
                md_content_for_conversion, metadata = plugin.before_markdown_conversion(
                    md_content_for_conversion, metadata, input_path_abs
                )
            except Exception as e:
                print(f"Error in plugin {plugin.__name__}.before_markdown_conversion: {e}")

    # Initialize MarkdownIt
    md_converter = MarkdownIt("gfm-like", {"linkify": True, "typographer": True, "html": True})
    md_converter.use(tasklists_plugin)
    md_converter.use(footnote_plugin)
    md_converter.use(strikethrough_plugin)
    md_converter.use(table_plugin)
    md_converter.use(admon_plugin) # Enable admonition plugin

    html_body_content = md_converter.render(md_content_for_conversion)

    # Manual .md to .html link rewriting
    soup_links = BeautifulSoup(html_body_content, 'html.parser')
    for a_tag in soup_links.find_all('a', href=True):
        href = a_tag['href']
        if href.endswith('.md'):
            # Ensure the link is relative to the current version path
            # e.g., if current_version_str is "v1.0", link becomes /v1.0/new.html
            # If href is absolute (/other.md), it should remain /other.html (no version prefix from here)
            # If href is relative (sub/doc.md), it becomes sub/doc.html within current version

            new_href = href[:-3] + '.html'

            # Prepend version path if link is not absolute and version exists
            # This logic might need refinement if links can be ../other_version/doc.md
            # For now, assume links are either root-relative (/) or page-relative.
            # If page-relative, it will correctly resolve within the version.
            # If root-relative (starts with /), it should NOT be versioned here,
            # unless it's meant to be a link to the root of the *current* version.
            # Let's assume for now that internal .md links are relative to current doc structure.
            # The make_url function handles global base_url and version string.
            # Here, we are just converting .md to .html.
            a_tag['href'] = new_href
    html_content_links_fixed = str(soup_links)

    # Pygments highlighting
    # This operates on html_content_links_fixed which is now html_body_content after link fixing
    soup_pygments = BeautifulSoup(html_content_links_fixed, 'html.parser')
    for pre_tag in soup_pygments.find_all('pre'):
        code_tag = pre_tag.find('code')
        if code_tag:
            code_class = code_tag.get('class', [])
            lang = None
            if code_class: # language-python
                lang = next((cls.replace('language-', '') for cls in code_class if cls.startswith('language-')), None)

            code_content_text = ''.join(code_tag.stripped_strings) # Get all text, even if nested
            if code_content_text:
                try:
                    lexer = get_lexer_by_name(lang, stripall=True) if lang else guess_lexer(code_content_text, stripall=True)
                    formatter = HtmlFormatter(nowrap=True, cssclass="highlight") # nowrap=True is key
                    highlighted_html_content = highlight(code_content_text, lexer, formatter)

                    # Replace code tag's content with new highlighted content
                    code_tag.clear() # Remove existing children/text
                    code_tag.append(BeautifulSoup(highlighted_html_content, 'html.parser'))
                except Exception as e:
                    print(f"Warning: Pygments highlighting failed for lang '{lang}' in {input_path_abs}: {e}")
    html_body_content = str(soup_pygments) # Content after pygments

    # Hook: after_html_generation (before copy buttons and table wrapping)
    for plugin in LOADED_PLUGINS:
        if hasattr(plugin, "after_html_generation"):
            try:
                html_body_content = plugin.after_html_generation(
                    html_body_content, metadata, input_path_abs
                )
            except Exception as e:
                print(f"Error in plugin {plugin.__name__}.after_html_generation: {e}")

    # Add copy buttons
    html_body_content = add_codeblock_copy_buttons(html_body_content)

    # Wrap tables
    soup_tables_final = BeautifulSoup(html_body_content, 'html.parser')
    for table_tag in soup_tables_final.find_all('table'):
        if not (table_tag.parent and table_tag.parent.get('class') and 'table-responsive' in table_tag.parent.get('class')):
            wrapper = soup_tables_final.new_tag('div', attrs={'class': 'table-responsive'})
            table_tag.wrap(wrapper)
    html_body_content = str(soup_tables_final) # This is the final body HTML

    # Extract H1 for title
    h1_tag = BeautifulSoup(html_body_content, 'html.parser').find('h1')
    page_title = h1_tag.text if h1_tag else os.path.splitext(os.path.basename(input_path_abs))[0].title()

    # Navigation HTML (pass current file relative to its input_dir)
    # input_dir_for_file_discovery is like 'docs/v1.0'
    # input_path_abs is like '/abs/path/to/docs/v1.0/sub/page.md'
    current_file_rel_to_version_input_dir = os.path.relpath(input_path_abs, input_dir_for_file_discovery)
    nav_links_html = build_navigation(input_path_abs, input_dir_for_file_discovery, current_version_str, all_versions_list) # Pass more args

    # Prev/Next links
    prev_link_html, next_link_html = get_prev_next_links(current_file_rel_to_version_input_dir, input_dir_for_file_discovery, current_version_str)


    # Edit on GitHub link
    edit_link_html_suffix = ""
    if add_edit_link and CONFIG.get("github", {}).get("repo"):
        repo = CONFIG["github"]["repo"]
        branch = CONFIG["github"].get("branch", "main")
        path_for_edit_link = os.path.relpath(input_path_abs, os.getcwd())
        edit_url = f"https://github.com/{repo}/edit/{branch}/{path_for_edit_link}"
        edit_link_html_suffix = f'\n<p class="edit-link"><a href="{edit_url}">Edit this page on GitHub</a></p>'
    
    # The $content for the template is html_body_content + edit_link_html_suffix
    content_for_template = html_body_content + edit_link_html_suffix


    # Page URL for canonical link (relative to version root, e.g., "mypage.html")
    output_dir_for_version = os.path.dirname(output_filename_abs)
    if os.path.basename(output_filename_abs) == "index.html" and os.path.basename(os.path.dirname(output_filename_abs)) == current_version_str:
         # This is the root index.html of the version, e.g. /v1.0/
        page_rel_path_for_make_url = ""
    else:
        # For other pages, it's relative to the version's output dir
        page_rel_path_for_make_url = os.path.relpath(output_filename_abs, output_dir_for_version)

    canonical_page_url = make_url(page_rel_path_for_make_url, version_aware=True)


    # Favicon URL: relative to site root if versioned, or just filename if not.
    # Base URL already includes version if VERSION_STRING is set globally for make_url.
    # So, make_url("favicon.png", version_aware=False) for site root favicon.
    # Or, if favicon is versioned, then make_url("favicon.png", version_aware=True).
    # Current setup copies static files (including favicon) into each version's output.
    # So, favicon_url should be relative to the version's root.
    # copy_static_files places a downloaded favicon into the root of the version's output dir.
    # So, make_url("favicon.png", version_aware=True) will correctly point to BASE_URL/VERSION/favicon.png
    # If building for root (no version_string), version_aware=False will point to BASE_URL/favicon.png
    favicon_url = make_url("favicon.png", version_aware=(current_version_str is not None))


    # Concatenated docs URL
    # This also resides at the root of the version's output directory.
    concat_docs_filename = CONFIG.get("concat_docs_filename", "concatenated_docs.txt")
    concat_docs_url = make_url(concat_docs_filename, version_aware=(current_version_str is not None))

    # Raw markdown for template
    raw_markdown_for_template = md_content_no_frontmatter # After frontmatter removal

    page_render_context = {
        "title": page_title,
        "canonical_url": canonical_page_url,
        "page_url": canonical_page_url,
        "content": content_for_template, # Use the combined content
        "project_name": CONFIG.get("project_name", CONFIG.get("project", "Untitled Project")),
        "description": metadata.get("description", CONFIG.get("description", "")), # Use metadata description if available
        "author": CONFIG.get("author", ""),
        "og_image": make_url(CONFIG.get("og_image", "social-card.png"), version_aware=False), # OG image usually at site root
        "twitter_handle": CONFIG.get("twitter_handle", ""),
        "version": CONFIG.get("version", current_version_str or "N/A"), # Use app version from config, fallback to current_version_str
        "current_version": current_version_str, # For version selector
        "all_versions": all_versions_list,      # For version selector
        "year": datetime.now().year,
        "repo_url": CONFIG.get("repo_url", ""),
        "navigation": nav_links_html,
        "prev_link": prev_link_html,
        "next_link": next_link_html,
        "base_url": temp_base_url_for_static, # Base URL for template links (e.g. to favicon, versions)
                                       # This should be the root base_url, not versioned one for template logic
        "favicon_url": favicon_url, # This should point to the versioned favicon
        "concat_docs_url": concat_docs_url,
        "raw_markdown_content": md_content_for_conversion, # Pass potentially plugin-modified markdown
        "config": CONFIG,
        "version_selector_html": ""
    }

    # Build version selector HTML (already done above, just re-assigning to keep flow)
    if all_versions_list and current_version_str:
        options_html = ""
        # Construct base path for version links. This should be relative to site root.
        # Example: if site is at example.com, base_path_for_versions = /
        # If site is at example.com/docs/, base_path_for_versions = /docs/
        # The make_url(rel_path="", version_aware=False) gives the site root URL.
        site_root_url = make_url("", version_aware=False)

        for ver in all_versions_list:
            # Value should be like /path/to/site/v1.0/ or /path/to/site/ (for root)
            # The make_url function with version_aware=True will build this.
            # We want the link to the index of that version.
            version_index_url = make_url("index.html", version_aware=(ver != "latest")) # Special handling for "latest"
            if ver == "latest": # "latest" should point to site root
                 version_index_url = site_root_url + "/" if site_root_url != "." else "./"


            selected_attr = 'selected' if ver == current_version_str else ''
            options_html += f'<option value="{version_index_url}" {selected_attr}>{ver}</option>'

        # Option for root/latest if not already part of all_versions_list in that exact form
        # Or if a "latest" version distinct from numbered versions is desired.
        # The current logic in build_all_versions.py might not add "latest" explicitly.
        # Let's assume for now the 'latest' option is handled by the loop if 'latest' is in all_versions_list.
        # If not, a static "latest" or "root" link can be added:
        # root_url = make_url("", version_aware=False) # This gives the base_url
        # options_html += f'<option value="{root_url}/">latest (root)</option>'
        # This needs to be coordinated with how build_all_versions.py structures versions.

        if options_html: # Only show selector if there are versions
            page_render_context["version_selector_html"] = f'''
<div class="version-selector" style="margin-left: 1em;">
    <label for="version-select" style="color: white; margin-right: 0.5em;">Version:</label>
    <select id="version-select" onchange="if (this.value) window.location.href = this.value;" style="padding: 0.3em; border-radius: 4px;">
        {options_html}
    </select>
</div>'''

    # Remove keys with None value to avoid issues with Template if $key is not handled
    # Also, ensure all keys expected by the template are present, even if empty string
    final_context = {**page_render_context}
    for key in TEMPLATE.pattern.groupindex.keys():
        if key not in final_context:
            final_context[key] = ""

    full_page_html_assembled = TEMPLATE.substitute(final_context)

    # Hook: after_full_page_assembly
    for plugin in LOADED_PLUGINS:
        if hasattr(plugin, "after_full_page_assembly"):
            try:
                full_page_html_assembled = plugin.after_full_page_assembly(
                    full_page_html_assembled, metadata, output_filename_abs
                )
            except Exception as e:
                print(f"Error in plugin {plugin.__name__}.after_full_page_assembly: {e}")

    os.makedirs(os.path.dirname(output_filename_abs), exist_ok=True)
    with open(output_filename_abs, "w", encoding="utf8") as f:
        f.write(full_page_html_assembled)


def get_page_nav_tuples(page_list_tuples, current_index):
    """Helper for prev/next from a list of (title, html_file_rel_path, md_file_abs_path) tuples."""
    prev_page_tuple = page_list_tuples[current_index - 1] if current_index > 0 else None
    next_page_tuple = page_list_tuples[current_index + 1] if current_index < len(page_list_tuples) - 1 else None
    return prev_page_tuple, next_page_tuple


def generate_concatenated_markdown(input_dir_to_use, output_dir_to_use, current_version_str):
    """Generates a single Markdown file from README.md and other .md files in input_dir_to_use."""
    all_markdown_content = []
    files_to_process = []

    readme_path = os.path.join(input_dir_to_use, "README.md")
    if os.path.exists(readme_path):
        files_to_process.append(readme_path)

    # Add other .md files from the root of input_dir_to_use
    # And recursively from subdirectories
    for root, _, files in os.walk(input_dir_to_use):
        for name in sorted(files):
            if name.endswith(".md"):
                file_abs_path = os.path.join(root, name)
                if file_abs_path not in files_to_process and name != "404.md": # Exclude 404 and already added README
                    files_to_process.append(file_abs_path)

    for filepath in files_to_process:
        try:
            with open(filepath, "r", encoding="utf8") as f:
                content = f.read()
            # Store file path relative to input_dir_to_use for clarity in concatenated file
            rel_filepath_for_header = os.path.relpath(filepath, input_dir_to_use)
            all_markdown_content.append(f"\n---\nFile: {rel_filepath_for_header}\n---\n\n{content}")
        except Exception as e:
            print(f"Warning: Could not read or process file {filepath} for concatenation: {e}")

    if not all_markdown_content:
        print(f"No Markdown files found in {input_dir_to_use} to concatenate.")
        return

    concatenated_content = "".join(all_markdown_content)

    # Output filename from global config, placed in versioned output directory
    output_filename_config = CONFIG.get("concat_docs_filename", "concatenated_docs.txt")
    full_output_path = os.path.join(output_dir_to_use, output_filename_config)

    os.makedirs(os.path.dirname(full_output_path), exist_ok=True)
    try:
        with open(full_output_path, "w", encoding="utf8") as f:
            f.write(concatenated_content)
        print(f"Generated concatenated docs: {full_output_path}")
    except Exception as e:
        print(f"Error writing concatenated Markdown file to {full_output_path}: {e}")


def main():
    parser = argparse.ArgumentParser(description=show_help.__doc__.format(input_dir=INPUT_DIR, output_dir=OUTPUT_DIR, version_string="{version_string}") or "Minimal Markdown to HTML static site generator")
    parser.add_argument("--input_dir", default=INPUT_DIR, help=f"Input directory for Markdown files (default: {INPUT_DIR})")
    parser.add_argument("--output_dir", default=OUTPUT_DIR, help=f"Output directory for HTML files (default: {OUTPUT_DIR})")
    parser.add_argument("--version_string", default=None, help="Version string (e.g., v1.0.0)")
    parser.add_argument("--all_versions_json", default="[]", help="JSON string of all available versions (e.g., '[\"v1.0\", \"v0.9\"]')")
    parser.add_argument("--regen-card", action="store_true", help="Force regenerate social card")
    args = parser.parse_args()

    global INPUT_DIR, OUTPUT_DIR, VERSION_STRING, ALL_VERSIONS, BASE_URL, LOADED_PLUGINS
    INPUT_DIR = args.input_dir
    OUTPUT_DIR = args.output_dir
    VERSION_STRING = args.version_string
    try:
        ALL_VERSIONS = json.loads(args.all_versions_json)
    except json.JSONDecodeError:
        print(f"Warning: Could not parse --all_versions_json: {args.all_versions_json}. Defaulting to empty list.")
        ALL_VERSIONS = []

    # Effective output directory, considering version
    effective_output_dir = OUTPUT_DIR
    if VERSION_STRING:
        effective_output_dir = os.path.join(OUTPUT_DIR, VERSION_STRING)
    
    # Update BASE_URL from config
    BASE_URL = CONFIG.get("base_url", ".").rstrip("/")

    # Load plugins
    load_plugins() # Populates LOADED_PLUGINS

    copy_static_files(effective_output_dir, INPUT_DIR)
    generate_concatenated_markdown(INPUT_DIR, effective_output_dir, VERSION_STRING)

    pages_for_sitemap = []
    search_data_items = [] # List of dicts for search index

    os.makedirs(effective_output_dir, exist_ok=True)

    # Social card generation (typically global, not per version, but output to versioned dir for now)
    social_card_config = CONFIG.get("social_card", {})
    # social-card.png should be relative to the versioned output directory for now
    social_card_path_in_output = pathlib.Path(effective_output_dir) / "social-card.png"

    # If og_image in config is just "social-card.png", it will be versioned by make_url if version_aware=True
    # We want the config's og_image to point to the *root* social card.
    # So, when generating the card, place it in effective_output_dir.
    # When filling template, og_image path should be constructed using make_url(..., version_aware=False)

    should_generate_card = args.regen_card or not social_card_config.get("image") or not social_card_path_in_output.exists()
    if should_generate_card:
        try:
            from generate_card import generate_social_card # Assuming generate_card.py is in PYTHONPATH
        except ImportError:
            print("Warning: generate_card.py not found. Skipping social card generation.")
        else:
            generate_social_card(
                title=social_card_config.get("title", CONFIG.get("project", "Project Title")),
                tagline=social_card_config.get("tagline", "Project Tagline"),
                output_path=str(social_card_path_in_output), # Generate into versioned output
                theme=social_card_config.get("theme", "light"),
                font=social_card_config.get("font", "Poppins")
            )
            print(f"Generated social card: {social_card_path_in_output}")

    # Ensure og_image in main CONFIG points to a root path for template context
    # The template will then use make_url(CONFIG.og_image, version_aware=False)
    if not CONFIG.get("og_image_is_absolute", False) and CONFIG.get("og_image"):
        # If og_image is like "social-card.png", it's fine, make_url handles it.
        pass
    elif not CONFIG.get("og_image"):
        # If no og_image set, and we generated one, point to the root version of it.
        CONFIG["og_image"] = "social-card.png" # It will be resolved by make_url at site root


    # Discover markdown files from INPUT_DIR
    # nav_page_tuples: list of (title, html_file_rel_to_version_output, md_file_abs_path)
    nav_page_tuples = []
    
    # README.md at the root of INPUT_DIR
    readme_md_abs_path = pathlib.Path(INPUT_DIR) / "README.md"
    if readme_md_abs_path.exists():
        readme_title = extract_title(readme_md_abs_path.read_text(encoding="utf8"))
        # HTML output will be index.html at the root of effective_output_dir
        nav_page_tuples.append((readme_title, "index.html", str(readme_md_abs_path)))

        # For search index (url is relative to version root)
        search_data_items.append({
            "title": readme_title,
            "content_md": remove_frontmatter(readme_md_abs_path.read_text(encoding="utf8")),
            "url": "index.html"
        })

    # Other .md files in INPUT_DIR (recursive)
    for root, _, files in os.walk(INPUT_DIR):
        for filename in sorted(files):
            if filename.endswith(".md") and filename != "README.md" and filename != "404.md":
                md_file_abs_path = pathlib.Path(root) / filename
                md_content_raw = md_file_abs_path.read_text(encoding="utf8")
                page_title = extract_title(md_content_raw)

                # Determine HTML output path relative to effective_output_dir
                # e.g. if INPUT_DIR=docs/v1, md_file_abs_path=docs/v1/sub/page.md
                # then html_file_rel_path should be sub/page.html
                md_file_rel_to_input_dir = md_file_abs_path.relative_to(INPUT_DIR)
                html_file_rel_path = str(md_file_rel_to_input_dir.with_suffix(".html"))

                nav_page_tuples.append((page_title, html_file_rel_path, str(md_file_abs_path)))

                search_data_items.append({
                    "title": page_title,
                    "content_md": remove_frontmatter(md_content_raw),
                    "url": html_file_rel_path # Relative to version root
                })

    # Convert all collected markdown files
    for i, (title, html_file_rel, md_abs_path) in enumerate(nav_page_tuples):
        prev_page_nav_info, next_page_nav_info = get_page_nav_tuples(nav_page_tuples, i)
        
        # output_filename_abs is like /path/to/docs/site/v1.0/page.html
        output_filename_abs = os.path.join(effective_output_dir, html_file_rel)

        convert_markdown_file(
            input_path_abs=md_abs_path,
            output_filename_abs=output_filename_abs,
            current_version_str=VERSION_STRING,
            all_versions_list=ALL_VERSIONS,
            add_edit_link=True, # Assuming edit link is always on for main docs
            prev_page_tuple=prev_page_nav_info, # This will be (title, html_rel_path, md_abs_path)
            next_page_tuple=next_page_nav_info, # This will be (title, html_rel_path, md_abs_path)
            input_dir_for_file_discovery=INPUT_DIR # Base input dir for this version
        )
        pages_for_sitemap.append(output_filename_abs) # Add absolute path for sitemap generation

    # Process 404.md if it exists in INPUT_DIR
    fourofour_md_path = pathlib.Path(INPUT_DIR) / "404.md"
    if fourofour_md_path.exists():
        fourofour_html_output_abs = pathlib.Path(effective_output_dir) / "404.html"
        convert_markdown_file(
            input_path_abs=str(fourofour_md_path),
            output_filename_abs=str(fourofour_html_output_abs),
            current_version_str=VERSION_STRING,
            all_versions_list=ALL_VERSIONS,
            add_edit_link=False,
            input_dir_for_file_discovery=INPUT_DIR
        )
        pages_for_sitemap.append(str(fourofour_html_output_abs))
        # Note: 404.html is typically at site root, not per version.
        # If a truly global 404 is needed, it should be handled outside version loop
        # or copied to the main site root (OUTPUT_DIR, not effective_output_dir)
        # For now, it's generated inside the version's output directory.

    generate_search_index(search_data_items, effective_output_dir) # Pass effective_output_dir
    write_sitemap_xml(pages_for_sitemap, effective_output_dir, VERSION_STRING) # Pass effective_output_dir & version

    # robots.txt should ideally be at the site root if it's global.
    # If each version is treated as a sub-site with its own sitemap, then placing it
    # inside effective_output_dir might be acceptable, but it means you'd have
    # example.com/v1.0/robots.txt.
    # For a single, global robots.txt at example.com/robots.txt, this call
    # should only happen when building the "main" or "latest" site, and
    # output_dir_to_use should be the true site root (args.output_dir).
    # Let's assume for now it's per-version, consistent with sitemap.
    write_robots_txt(effective_output_dir)


if __name__ == "__main__":
    main()
