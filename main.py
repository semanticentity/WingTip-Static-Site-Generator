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
  ./sitemap.txt        -> plain sitemap for all .html files

REQUIREMENTS:
  pip install markdown beautifulsoup4

NOTES:
  - Adds top-right Docs link
  - Adds custom favicon support
  - Adds light/dark mode toggle
  - Adds TOC, .md link rewrite, GitHub edit link
  - Adds copy buttons to all code blocks
  - Adds sitemap.xml generation:
    - export WINGTIP_BASE_URL=https://yourusername.github.io/yourrepo
    - sitemap.xml will be generated in ./docs/site/sitemap.xml
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
    "version": "0.1.0",
    "repo_url": "",
}
CFG_PATH = pathlib.Path(__file__).parent / "config.json"
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

# Helper to build canonical URLs
def make_url(rel_path):
    rel_path = rel_path.lstrip("/")
    if rel_path == "index.html":
        rel_path = ""
    return f"{BASE_URL}/{rel_path}".rstrip("/")

def write_robots_txt():
    lines = ["User-agent: *", "Allow: /"]
    if BASE_URL:
        lines.append(f"Sitemap: {BASE_URL}/sitemap.xml")
    with open(os.path.join(OUTPUT_DIR, "robots.txt"), "w", encoding="utf8") as f:
        f.write("\n".join(lines))

def write_sitemap_xml(pages):
    with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), "w", encoding="utf8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for path in pages:
            rel_path = path.replace(OUTPUT_DIR + "/", "").lstrip("/")
            f.write(f'  <url><loc>{BASE_URL}/{rel_path}</loc></url>\n')
        f.write('</urlset>\n')

def copy_static_files():
    """Copy static files to output directory"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # Copy pygments.css
    source = os.path.join(os.path.dirname(__file__), "pygments.css")
    dest = os.path.join(OUTPUT_DIR, "pygments.css")
    if os.path.exists(source):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(source, "rb") as fsrc, open(dest, "wb") as fdst:
            fdst.write(fsrc.read())
    
    # Handle favicon
    favicon_dest = os.path.join(OUTPUT_DIR, "favicon.png")
    if CONFIG.get("favicon"):
        try:
            import urllib.request
            urllib.request.urlretrieve(CONFIG["favicon"], favicon_dest)
        except Exception as e:
            print(f"Warning: Failed to download favicon: {e}")

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
    docs_dir = os.path.join(os.path.dirname(__file__), 'docs')
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

def convert_markdown_file(input_path, output_filename, add_edit_link=False, prev_page=None, next_page=None):
    with open(input_path, "r", encoding="utf8") as f:
        md = f.read()

    # Convert markdown to HTML
    html = markdown.markdown(
        md,
        extensions=["fenced_code", "codehilite", "tables"],
        output_format="html5"
    )

    # Add copy buttons to code blocks
    html = add_codeblock_copy_buttons(html)

    # Get the title from the first h1 in the markdown
    soup = BeautifulSoup(html, 'html.parser')
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
        base_url=BASE_URL
    )

    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    with open(output_filename, "w", encoding="utf8") as f:
        f.write(page)

def write_docs_index(doc_files):
    # Convert README to HTML
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf8") as f:
            readme_md = f.read()
        content = markdown.markdown(readme_md, extensions=["fenced_code", "codehilite", "tables"])
    else:
        content = "<p>No README.md found.</p>"

    # Add navigation section
    nav_html = ['<div class="navigation">']  
    nav_html.append('<h2>Navigation</h2>')
    nav_html.append('<ul>')
    
    # Add link to README/index
    nav_html.append('<li><a href="index.html">README</a></li>')
    
    # Add links to all docs
    docs_dir = "docs"
    if os.path.isdir(docs_dir):
        for name in os.listdir(docs_dir):
            if name.endswith(".md"):
                base = os.path.splitext(name)[0]
                nav_html.append(f'<li><a href="{base}.html">{base}</a></li>')
    
    nav_html.append('</ul>')
    nav_html.append('</div>')
    content += '\n' + '\n'.join(nav_html)

    # Create the index page content
    content = f"""
    <div class="docs-index">
        <div class="left-col">
            {content}
        </div>
    </div>
    """

    # Write the index page
    page = TEMPLATE.substitute(
        title="Navigation",
        canonical_url=f"{BASE_URL}/docs/",
        page_url="docs/",
        content=content,
        project=CONFIG["project"],
        description=CONFIG["description"],
        author=CONFIG["author"],
        og_image=CONFIG["og_image"],
        twitter_handle=CONFIG["twitter_handle"],
    )

    os.makedirs(os.path.join(OUTPUT_DIR, "docs"), exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "docs", "index.html"), "w", encoding="utf8") as f:
        f.write(page)

def get_page_nav(pages, current_index):
    """Get previous and next page links"""
    prev_page = pages[current_index - 1] if current_index > 0 else None
    next_page = pages[current_index + 1] if current_index < len(pages) - 1 else None
    return prev_page, next_page

def main():
    parser = argparse.ArgumentParser(description=show_help.__doc__ or "Minimal Markdown to HTML static site generator")
    parser.add_argument("--regen-card", action="store_true", help="Force regenerate social card")
    parser.add_argument("--output", help="Output directory (default: docs/site)")
    args = parser.parse_args()
    
    # Update output dir if specified
    global OUTPUT_DIR
    if args.output:
        OUTPUT_DIR = args.output

    copy_static_files()
    pages = []
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
            title = extract_title(f.read())
        nav_pages.append((title, "index.html", "README.md"))
    
    # Then collect all .md files from docs directory
    if os.path.isdir(docs_dir):
        for name in os.listdir(docs_dir):
            if name.endswith(".md"):
                md_path = os.path.join(docs_dir, name)
                with open(md_path, "r", encoding="utf8") as f:
                    title = extract_title(f.read())
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



    write_sitemap_xml(pages)
    write_robots_txt()

if __name__ == "__main__":
    main()
