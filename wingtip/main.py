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
from datetime import datetime, date, timezone
from email.utils import format_datetime
import yaml 
import subprocess
from .latex_extension import LaTeXPreservationExtension

_last_modified_cache = {}

def get_last_modified(filepath: str) -> str:
    """
    Get the last modified date of a file from git history (ISO 8601 format).
    Falls back to file mtime if git is not available or the file is uncommitted.
    Note: Requires checkout fetch-depth: 0 in CI to work correctly.
    """
    if filepath in _last_modified_cache:
        return _last_modified_cache[filepath]

    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%cI', filepath],
            capture_output=True,
            text=True,
            check=True
        )
        out = result.stdout.strip()
        if out:
            _last_modified_cache[filepath] = out
            return out
    except Exception:
        pass

    try:
        mtime = os.path.getmtime(filepath)
        dt = datetime.fromtimestamp(mtime).isoformat()
        if not dt.endswith('Z') and '+' not in dt:
            dt += '+00:00'
        _last_modified_cache[filepath] = dt
        return dt
    except OSError:
        now = datetime.now().isoformat()
        if not now.endswith('Z') and '+' not in now:
            now += '+00:00'
        return now

def _parse_datetime(value):
    """Parse a YAML/string/datetime value into a datetime object."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, str):
        text = value.strip()
        # ISO-8601 (Python 3.7+ supports 'Z' via replace)
        try:
            return datetime.fromisoformat(text.replace('Z', '+00:00'))
        except ValueError:
            pass
        for fmt in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d'):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
    return None

def _iso_date(value):
    dt = _parse_datetime(value)
    return dt.isoformat() if dt else ''

def _display_date(value):
    dt = _parse_datetime(value)
    return dt.strftime('%B %d, %Y') if dt else ''

OUTPUT_DIR = "docs/site"

def show_help():
    """Build portable, SEO-first documentation sites from Markdown.

WingTip converts README.md and the docs/ tree (discovered recursively, with
nested paths preserved in URLs) into static HTML with local search, structured
data, RSS, sitemaps, AI-readable Markdown artifacts, and optional offline
support. Generated output can be hosted on any static file server.
"""
    print(show_help.__doc__)

def _package_version(default="0.0.0"):
    """Read the version from installed metadata or a source checkout."""
    try:
        from importlib.metadata import version
        return version("wingtip")
    except Exception:
        pass

    try:
        pyproject = pathlib.Path(__file__).resolve().parents[1] / "pyproject.toml"
        match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', pyproject.read_text(encoding="utf8"), re.MULTILINE)
        if match:
            return match.group(1)
    except Exception:
        pass
    return default


# Load config
DEFAULT_CONFIG = {
    # base_url MUST have a default. It is read at import time, so a missing key
    # here is not a feature failure -- it is `wingtip --help` raising KeyError.
    # "." yields relative URLs, which is what you want for local preview.
    "base_url": ".",
    # Canonical key is project_name. "project" is kept as a legacy alias and
    # normalised below; everything downstream reads project_name.
    "project_name": "Documentation",
    "tagline": "",
    "description": "",
    "author": "",
    "og_image": "social-card.png",
    "twitter_handle": "",
    "concat_docs_filename": "llms-full.txt",
    "version": _package_version(),
    "repo_url": "",
}
CFG_PATH = pathlib.Path("config.json")
CONFIG = DEFAULT_CONFIG.copy()
if CFG_PATH.exists():
    CONFIG.update(json.loads(CFG_PATH.read_text()))

# Reconcile the legacy "project" alias with project_name so old configs and old
# template vars both keep working, and neither can silently resolve to "".
if CONFIG.get("project") and not CONFIG.get("project_name"):
    CONFIG["project_name"] = CONFIG["project"]
CONFIG["project_name"] = CONFIG.get("project_name") or "Documentation"
CONFIG["project"] = CONFIG["project_name"]

THEME_CFG_PATH = pathlib.Path("theme.json")
THEME_CONFIG = {}
_PLUGINS = []  # populated at build time
if THEME_CFG_PATH.exists():
    try:
        THEME_CONFIG = json.loads(THEME_CFG_PATH.read_text())
    except json.JSONDecodeError as e:
        print(f"Warning: Could not parse theme.json: {e}. Using default theme.")

BASE_URL = (CONFIG.get("base_url") or ".").rstrip("/") or "."

import importlib
import importlib.resources

# Load and format template
def load_template():
    try:
        raw = importlib.resources.read_text("wingtip", "template.html", encoding="utf8")
    except AttributeError:
        # Fallback for Python 3.11+
        raw = importlib.resources.files("wingtip").joinpath("template.html").read_text(encoding="utf8")
    except Exception:
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

def write_llms_txt(nav_pages):
    """Generates llms.txt index following the llmstxt.org specification."""
    lines = []
    lines.append(f"# {CONFIG.get('project', 'Project')}")
    description = CONFIG.get("description")
    if description:
        lines.append(f"\n> {description}\n")

    for title, html_file, md_path, _front in nav_pages:
        lines.append(f"- [{title}]({html_file})")

    lines.append("\n## Optional\n")
    concat_docs_filename = CONFIG.get("concat_docs_filename", "llms-full.txt")
    lines.append(f"- [{CONFIG.get('project', 'Project')} Full Documentation]({concat_docs_filename})")

    output_path = os.path.join(OUTPUT_DIR, "llms.txt")
    with open(output_path, "w", encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Generated llms.txt: {output_path}")

def write_robots_txt():
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /search_index.json",
        f"Allow: /{CONFIG.get('concat_docs_filename', 'llms-full.txt')}",
        "Allow: /llms.txt"
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
        for path, md_path in pages:
            rel_path = path.replace(OUTPUT_DIR + "/", "").lstrip("/")
            f.write(f'  <url>\n    <loc>{BASE_URL}/{rel_path}</loc>\n')
            if md_path and os.path.exists(md_path):
                lastmod_iso = get_last_modified(md_path)
                # Parse the iso string and format to YYYY-MM-DD
                lastmod_dt = datetime.fromisoformat(lastmod_iso.replace('Z', '+00:00'))
                lastmod = lastmod_dt.strftime('%Y-%m-%d')
                f.write(f'    <lastmod>{lastmod}</lastmod>\n')
            f.write('  </url>\n')
        f.write('</urlset>\n')

def _rss_date(value, md_path=None):
    """Parse a frontmatter/string value into an RFC-822 datetime string."""
    dt = _parse_datetime(value)
    if not dt and md_path:
        dt = _parse_datetime(get_last_modified(md_path))
    if not dt:
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return format_datetime(dt)

def _page_text_excerpt(md_text):
    """Return a short plain-text excerpt from markdown body."""
    # Remove front matter
    text = remove_frontmatter(md_text)
    # Collapse whitespace and take first sentence/line up to ~300 chars
    text = re.sub(r'\n+', ' ', text).strip()
    if not text:
        return ''
    if len(text) > 300:
        text = text[:297] + '...'
    return text

def generate_rss_feed(pages, output_dir):
    """Generate an RSS 2.0 feed for public pages that are not noindex."""
    feed_filename = CONFIG.get('rss_filename', 'feed.xml')
    output_path = os.path.join(output_dir, feed_filename)
    os.makedirs(output_dir, exist_ok=True)

    site_title = html_module.escape(CONFIG.get('project_name') or 'Documentation')
    site_link = BASE_URL if BASE_URL != '.' else ''
    site_desc = html_module.escape(CONFIG.get('description') or site_title)
    language = CONFIG.get('language', 'en')
    build_date = format_datetime(datetime.now(timezone.utc))

    items = []
    for html_path, md_path in pages:
        if not os.path.exists(md_path):
            continue
        with open(md_path, 'r', encoding='utf8') as f:
            md_text = f.read()
        front = parse_frontmatter(md_text)
        # Skip noindex pages in feed
        robots = front.get('robots', '')
        if front.get('noindex') or (isinstance(robots, str) and 'noindex' in robots.lower()):
            continue

        title = html_module.escape(str(front.get('title') or extract_title(md_text)))
        rel_path = html_path.replace(output_dir + '/', '').lstrip('/')
        link = f"{site_link}/{rel_path}" if site_link else rel_path
        description = html_module.escape(
            str(front.get('description') or _page_text_excerpt(md_text))
        )

        pub_date = _rss_date(front.get('date') or front.get('published'), md_path=md_path)
        guid = link

        items.append((pub_date, f"""    <item>
      <title>{title}</title>
      <link>{link}</link>
      <guid>{guid}</guid>
      <description>{description}</description>
      <pubDate>{pub_date}</pubDate>
    </item>"""))

    # Sort by publication date descending
    items.sort(key=lambda x: x[0], reverse=True)
    item_xml = '\n'.join(item[1] for item in items)

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{site_title}</title>
    <link>{site_link}</link>
    <description>{site_desc}</description>
    <language>{language}</language>
    <lastBuildDate>{build_date}</lastBuildDate>
    <generator>WingTip</generator>
{item_xml}
  </channel>
</rss>
"""
    with open(output_path, 'w', encoding='utf8') as f:
        f.write(rss)
    print(f"Generated RSS feed: {output_path}")

def get_theme_colors():
    """Return (theme_color, background_color) from the theme config."""
    light = THEME_CONFIG.get('light_mode', {})
    return light.get('links_or_primary', '#0366d6'), light.get('background_body', '#ffffff')

def _public_url(rel_path):
    """Shortcut to resolve a site-root relative path to a public URL."""
    return resolve_public_url(rel_path)

def _build_head_snippet(front_matter):
    """Build a custom <head> snippet from analytics config, global snippets, and per-page frontmatter."""
    snippets = []

    analytics = CONFIG.get('analytics') or {}
    provider = str(analytics.get('provider') or analytics.get('type') or '').lower().strip()
    site_id = str(analytics.get('site_id') or analytics.get('id') or analytics.get('property_id') or analytics.get('tracking_id') or '')
    domain = str(analytics.get('domain') or analytics.get('site') or CONFIG.get('base_url') or '')

    if provider == 'plausible':
        src = str(analytics.get('src') or analytics.get('script') or 'https://plausible.io/js/plausible.js')
        snippets.append(f'<script defer data-domain="{html_module.escape(domain)}" src="{html_module.escape(src)}"></script>')
    elif provider == 'umami':
        src = str(analytics.get('src') or analytics.get('script') or 'https://analytics.umami.is/script.js')
        snippets.append(f'<script defer src="{html_module.escape(src)}" data-website-id="{html_module.escape(site_id)}"></script>')
    elif provider == 'fathom':
        src = str(analytics.get('src') or analytics.get('script') or 'https://cdn.usefathom.com/script.js')
        snippets.append(f'<script src="{html_module.escape(src)}" data-site="{html_module.escape(site_id)}" defer></script>')
    elif provider in ('gtag', 'google', 'googleanalytics'):
        if site_id:
            ga_id = html_module.escape(site_id)
            snippets.append(f"""<script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{ga_id}');
</script>""")
    elif provider == 'custom' and analytics.get('script'):
        snippets.append(str(analytics['script']))

    # Global head snippet from config (file path or raw HTML)
    for key in ('head_snippet', 'head'):
        config_snippet = CONFIG.get(key)
        if isinstance(config_snippet, str):
            if os.path.exists(config_snippet):
                try:
                    snippets.append(pathlib.Path(config_snippet).read_text(encoding='utf8'))
                except Exception as e:
                    print(f"Warning: Could not read head snippet file {config_snippet}: {e}")
            else:
                snippets.append(config_snippet)

    # Per-page head snippet from frontmatter
    page_snippet = front_matter.get('head') or front_matter.get('head_snippet')
    if isinstance(page_snippet, str):
        snippets.append(page_snippet)
    elif isinstance(page_snippet, list):
        snippets.extend(str(s) for s in page_snippet)

    return '\n'.join(snippets)

def _build_hreflang_alternates(front_matter, canonical_url):
    """Build <link rel=\"alternate\" hreflang=...> tags from frontmatter / config."""
    if not canonical_url:
        return ''
    translations = front_matter.get('translations') or front_matter.get('hreflang') or {}
    if not isinstance(translations, dict):
        translations = {}
    i18n_config = CONFIG.get('i18n') or {}
    site_languages = i18n_config.get('languages', [])

    alts = {}
    for code, url in translations.items():
        alts[str(code).strip()] = str(url).strip()
    for lang_info in site_languages:
        if isinstance(lang_info, dict):
            code = str(lang_info.get('code', '')).strip()
            url = lang_info.get('url')
            if code and url and code not in alts:
                alts[code] = str(url).strip()

    if not alts:
        return ''

    current_lang = str(front_matter.get('lang') or front_matter.get('language') or CONFIG.get('language', 'en')).strip()
    links = [f'<link rel="alternate" hreflang="{html_module.escape(current_lang)}" href="{html_module.escape(canonical_url)}">']
    for code, url in alts.items():
        links.append(f'<link rel="alternate" hreflang="{html_module.escape(code)}" href="{html_module.escape(resolve_public_url(url))}">')
    links.append(f'<link rel="alternate" hreflang="x-default" href="{html_module.escape(canonical_url)}">')
    return '\n  '.join(links)

def _load_plugins():
    """Load user plugins from the plugins/ directory.

    The optional `plugins` config key can be a list of module basenames to load.
    If omitted, all *.py files in plugins/ are loaded.
    """
    plugins = []
    plugins_dir = pathlib.Path("plugins")
    if not plugins_dir.is_dir():
        return plugins
    allowed = CONFIG.get('plugins')
    if not isinstance(allowed, list):
        allowed = None
    for plugin_file in sorted(plugins_dir.glob("*.py")):
        if plugin_file.name.startswith("_"):
            continue
        if allowed and plugin_file.stem not in allowed:
            continue
        module_name = f"__wingtip_user_plugins_{plugin_file.stem}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            plugins.append(module)
        except Exception as e:
            print(f"Warning: Could not load plugin {plugin_file}: {e}")
    return plugins

def _plugin_markdown_extensions(plugins):
    """Collect Markdown extension objects/strings from plugins."""
    extensions = []
    for plugin in plugins:
        exts = getattr(plugin, 'markdown_extensions', [])
        if callable(exts) and not isinstance(exts, (list, tuple)):
            try:
                exts = exts()
            except Exception as e:
                print(f"Warning: markdown_extensions hook failed in {plugin.__name__}: {e}")
                exts = []
        if isinstance(exts, (list, tuple)):
            extensions.extend(exts)
    return extensions

def _build_csp(front_matter):
    """Build a Content-Security-Policy string from config and per-page frontmatter."""
    csp = front_matter.get('csp')
    if csp is None:
        csp = CONFIG.get('csp', False)
    if csp is False or csp is None:
        return ''
    if isinstance(csp, str):
        return csp.strip()
    if isinstance(csp, dict):
        return str(csp.get('policy', '')).strip()

    # Default CSP tuned for WingTip's bundled and CDN assets.
    # 'unsafe-inline' is required because the template uses inline scripts/styles.
    analytics = CONFIG.get('analytics') or {}
    providers = {
        'plausible': 'https://plausible.io',
        'umami': str(analytics.get('src', 'https://analytics.umami.is')).rsplit('/script.js', 1)[0],
        'fathom': 'https://cdn.usefathom.com',
        'gtag': 'https://www.googletagmanager.com https://www.google-analytics.com https://*.google-analytics.com',
        'google': 'https://www.googletagmanager.com https://www.google-analytics.com https://*.google-analytics.com',
        'googleanalytics': 'https://www.googletagmanager.com https://www.google-analytics.com https://*.google-analytics.com'
    }
    provider = str(analytics.get('provider') or analytics.get('type') or '').lower().strip()
    connect_extra = providers.get(provider, '')
    script_extra = connect_extra

    if provider == 'plausible':
        plausible_src = str(analytics.get('src', 'https://plausible.io/js/plausible.js'))
        script_extra = f"{connect_extra} {plausible_src}"
    elif provider == 'umami':
        umami_src = str(analytics.get('src', 'https://analytics.umami.is/script.js'))
        script_extra = f"{connect_extra} {umami_src}"
    elif provider == 'fathom':
        fathom_src = str(analytics.get('src', 'https://cdn.usefathom.com/script.js'))
        script_extra = f"{connect_extra} {fathom_src}"

    return (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
        f"{script_extra.strip()}; "
        "style-src 'self' 'unsafe-inline'; "
        "font-src 'self'; "
        "img-src 'self' data: https:; "
        f"connect-src 'self' {connect_extra.strip()}; "
        "media-src 'self'; "
        "manifest-src 'self'; "
        "worker-src 'self'; "
        "child-src 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "upgrade-insecure-requests;"
    )

def generate_pwa_files(pages, output_dir):
    """Generate a web app manifest, PWA icons, offline fallback, and service worker."""
    os.makedirs(output_dir, exist_ok=True)
    theme_color, background_color = get_theme_colors()
    project_name = CONFIG.get('project_name') or 'Documentation'
    short_name = project_name[:12]
    description = CONFIG.get('description') or project_name
    language = CONFIG.get('language', 'en')

    manifest_path = pathlib.Path(output_dir) / "manifest.json"
    sw_path = pathlib.Path(output_dir) / "sw.js"
    offline_path = pathlib.Path(output_dir) / "offline.html"

    # Generate icon sizes from favicon.png / wingtip-logo.png if available
    icon_192 = "icon-192.png"
    icon_512 = "icon-512.png"
    source_icon = None
    # Only use a favicon explicitly supplied by the project; no packaged fallback.
    for candidate in ('favicon.png', os.path.join(output_dir, 'favicon.png')):
        if os.path.exists(candidate):
            source_icon = candidate
            break
    if source_icon:
        try:
            from PIL import Image
            # Ensure a favicon exists in the site root for the manifest/PWA
            root_favicon = os.path.join(output_dir, 'favicon.png')
            if source_icon != root_favicon and not os.path.exists(root_favicon):
                shutil.copy2(source_icon, root_favicon)
            for size, filename in ((192, icon_192), (512, icon_512)):
                with Image.open(source_icon) as img:
                    if img.mode not in ('RGBA', 'RGB'):
                        img = img.convert('RGBA')
                    img_resized = img.resize((size, size), Image.LANCZOS)
                    img_resized.save(os.path.join(output_dir, filename), 'PNG')
        except Exception as e:
            print(f"Warning: Could not generate PWA icons from {source_icon}: {e}")
            icon_192 = ""
            icon_512 = ""
    else:
        icon_192 = ""
        icon_512 = ""

    # Build precache list from the generated output directory
    precache = []
    for root, dirs, files in os.walk(output_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for name in files:
            full = os.path.join(root, name)
            rel = os.path.relpath(full, output_dir).replace(os.sep, '/')
            if rel == 'sw.js':
                continue
            precache.append(rel)

    # Generate manifest
    icons_list = []
    if icon_192:
        icons_list.append({"src": icon_192, "sizes": "192x192", "type": "image/png"})
    if icon_512:
        icons_list.append({"src": icon_512, "sizes": "512x512", "type": "image/png"})
    manifest = {
        "name": project_name,
        "short_name": short_name,
        "description": description,
        "start_url": ".",
        "scope": ".",
        "display": "standalone",
        "background_color": background_color,
        "theme_color": theme_color,
        "orientation": "portrait",
        "lang": language,
        "icons": icons_list
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf8')
    print(f"Generated manifest: {manifest_path}")

    # Generate offline fallback page
    home_url = "./index.html" if BASE_URL == '.' else f"{BASE_URL}/index.html"
    offline_html = f"""<!DOCTYPE html>
<html lang="{html_module.escape(language)}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Offline · {html_module.escape(project_name)}</title>
  <meta name="theme-color" content="{html_module.escape(theme_color)}">
  <style>
    body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 2rem; background: {html_module.escape(background_color)}; color: #24292e; }}
    main {{ max-width: 720px; margin: auto; }}
    a {{ color: {html_module.escape(theme_color)}; }}
  </style>
</head>
<body>
  <main>
    <h1>You are offline</h1>
    <p>The page you requested is not available without a network connection.</p>
    <p><a href="{html_module.escape(home_url)}">Go to the home page</a></p>
  </main>
</body>
</html>"""
    offline_path.write_text(offline_html, encoding='utf8')

    # Generate service worker
    cache_version = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    urls_json = json.dumps(precache)
    sw_js = f"""const CACHE_VERSION = '{cache_version}';
const CACHE_NAME = 'wingtip-cache-' + CACHE_VERSION;

const PRECACHE_URLS = {urls_json};

self.addEventListener('install', (event) => {{
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {{
      return cache.addAll(PRECACHE_URLS);
    }}).then(() => self.skipWaiting())
  );
}});

self.addEventListener('activate', (event) => {{
  event.waitUntil(
    caches.keys().then((keyList) => {{
      return Promise.all(keyList.map((key) => {{
        if (key !== CACHE_NAME) {{
          return caches.delete(key);
        }}
      }}));
    }}).then(() => self.clients.claim())
  );
}});

self.addEventListener('fetch', (event) => {{
  if (event.request.method !== 'GET') return;
  if (!event.request.url.startsWith(self.location.origin)) return;

  event.respondWith(
    caches.match(event.request).then((cached) => {{
      if (cached) return cached;
      return fetch(event.request).then((response) => {{
        if (!response || response.status !== 200 || response.type !== 'basic') return response;
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        return response;
      }}).catch(() => {{
        if (event.request.mode === 'navigate') {{
          return caches.match('offline.html');
        }}
      }});
    }})
  );
}});
"""
    sw_path.write_text(sw_js, encoding='utf8')
    print(f"Generated service worker: {sw_path}")

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

def package_static_dir():
    """Absolute path to the static assets shipped inside the wingtip package.

    Mirrors load_template()'s resolution: importlib.resources when installed,
    __file__ when running from a checkout.
    """
    try:
        return str(importlib.resources.files("wingtip").joinpath("static"))
    except Exception:
        pass
    local = os.path.join(os.path.dirname(__file__), "static")
    return local if os.path.isdir(local) else None


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

    # Static assets resolve in two layers:
    #
    #   1. package defaults  (wingtip/static/)  -- always present once installed
    #   2. project overlay   (./static/)        -- optional, wins on conflict
    #
    # Layer 1 is why `pip install wingtip` produces a styled site. Before this,
    # copy_static_files() only ever looked at CWD, so an installed user's pages
    # requested static/css/custom.css and got three 404s and an unstyled site.
    static_dest_dir = os.path.join(OUTPUT_DIR, "static")

    if os.path.exists(static_dest_dir):
        if os.path.isdir(static_dest_dir):
            shutil.rmtree(static_dest_dir)
        else:
            os.remove(static_dest_dir)

    copied_from = []

    pkg_static = package_static_dir()
    if pkg_static and os.path.isdir(pkg_static):
        try:
            shutil.copytree(pkg_static, static_dest_dir)
            copied_from.append("package defaults")
        except Exception as e:
            print(f"Warning: Could not copy bundled static assets: {e}")

    project_static = "static"
    if os.path.isdir(project_static):
        try:
            shutil.copytree(project_static, static_dest_dir, dirs_exist_ok=True)
            copied_from.append(f"'{project_static}'")
        except Exception as e:
            print(f"Warning: Could not copy static assets from '{project_static}': {e}")

    if copied_from:
        print(f"Copied static assets ({' + '.join(copied_from)}) to '{static_dest_dir}'")
    else:
        print("Warning: no static assets found; pages will render unstyled.")

    # If the project provides a favicon in its root, copy it to the output root
    # so the favicon meta tag and PWA manifest can resolve it locally.
    if os.path.isfile('favicon.png'):
        try:
            shutil.copy2('favicon.png', os.path.join(OUTPUT_DIR, 'favicon.png'))
            print("Copied favicon.png to output root")
        except Exception as e:
            print(f"Warning: Could not copy favicon.png: {e}")


def parse_frontmatter(md_text):
    """Parse YAML front matter if present and return a dict."""
    if md_text.startswith('---'):
        try:
            end_marker = md_text.find('---', 3)
            if end_marker != -1:
                return yaml.safe_load(md_text[3:end_marker].strip()) or {}
        except Exception as e:
            print(f"Warning: Error parsing front matter: {e}")
    return {}


def resolve_public_url(path_or_url, default=None):
    """Resolve a config/frontmatter asset path into a public URL."""
    if not path_or_url and default:
        path_or_url = default
    if not path_or_url:
        return ''
    if path_or_url.startswith(('http://', 'https://')):
        return path_or_url
    rel = path_or_url
    while rel.startswith('./'):
        rel = rel[2:]
    if rel.startswith('/'):
        rel = rel[1:]
    if BASE_URL == '.':
        return rel
    return f"{BASE_URL}/{rel}"


def _slugify(name):
    """Simple ASCII slug generator."""
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', name.lower())
    return slug.strip('-')

def _doc_html_filename(md_path, docs_dir='docs'):
    """Convert a markdown source path to its output HTML path.

    Nested source paths are preserved in generated URLs
    (docs/guides/intro.md -> guides/intro.html) so existing site structures
    and inbound links survive a migration. A README.md maps to index.html
    within its directory.
    """
    if md_path == 'README.md':
        return 'index.html'
    rel = os.path.relpath(md_path, docs_dir)
    if rel.startswith('..'):
        # Source outside docs/ (e.g. 404.md in the project root)
        rel = os.path.basename(md_path)
    rel = rel.replace(os.sep, '/')
    dirname, _, basename = rel.rpartition('/')
    if basename.lower() == 'readme.md':
        basename = 'index.md'
    stem = os.path.splitext(basename)[0]
    return f"{dirname}/{stem}.html" if dirname else f"{stem}.html"

def _discover_doc_files(docs_dir='docs'):
    """Recursively find markdown files under docs_dir in stable sorted order.

    Skips hidden and underscore-prefixed directories and never descends into
    the build output directory (docs/site by default lives inside docs/).
    """
    found = []
    if not os.path.isdir(docs_dir):
        return found
    out_abs = os.path.abspath(OUTPUT_DIR)
    for dirpath, dirnames, filenames in os.walk(docs_dir):
        dirnames[:] = sorted(
            d for d in dirnames
            if not d.startswith(('.', '_'))
            and os.path.abspath(os.path.join(dirpath, d)) != out_abs
        )
        for name in sorted(filenames):
            if name.endswith('.md'):
                found.append(os.path.join(dirpath, name))
    return found

def _rel_href(from_rel, to_rel):
    """Relative URL from one output-relative page path to another."""
    rel = os.path.relpath(to_rel, os.path.dirname(from_rel) or '.')
    return rel.replace(os.sep, '/')

def _load_category_meta(category_dir):
    """Read _category.json metadata if present."""
    category_json = os.path.join(category_dir, '_category.json')
    if os.path.exists(category_json):
        try:
            return json.loads(pathlib.Path(category_json).read_text(encoding='utf8'))
        except Exception as e:
            print(f"Warning: Could not read {category_json}: {e}")
    return {}

def _category_for_path(md_path, docs_dir='docs', front_matter=None):
    """Return (category_slug, category_name) for a markdown file."""
    if front_matter and front_matter.get('category'):
        category_value = front_matter['category']
        if isinstance(category_value, dict):
            return (_slugify(category_value.get('name', 'category')), str(category_value.get('name', 'category')))
        name = str(category_value).strip()
        return (_slugify(name), name)

    # Determine the first-level subdirectory under docs/
    abs_md = os.path.abspath(md_path)
    abs_docs = os.path.abspath(docs_dir)
    if abs_md.startswith(abs_docs + os.sep):
        rel = os.path.relpath(abs_md, abs_docs)
        first = rel.split(os.sep)[0]
        if first and first != os.path.basename(rel):
            meta = _load_category_meta(os.path.join(docs_dir, first))
            name = meta.get('name') or first.replace('-', ' ').replace('_', ' ').title()
            return (_slugify(name), name)
    return None, None

def extract_title(md):
    front = parse_frontmatter(md)
    if front.get('title'):
        return str(front['title']).strip()
    match = re.search(r"^# (.+)", md, re.MULTILINE)
    return match.group(1).strip() if match else "Untitled"



_NAV_CACHE = None

def _nav_page_order(front):
    """Numeric sort order from `order`/`nav_order` frontmatter, or None."""
    value = front.get('order', front.get('nav_order')) if isinstance(front, dict) else None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def _sorted_nav_pages(entries):
    """Order pages by explicit `order` frontmatter first, then title."""
    return sorted(entries, key=lambda p: (p['order'] is None, p['order'] or 0, p['title'].lower()))

def _collect_nav_data(docs_dir='docs'):
    """Build the navigation model once per build.

    Returns (tree, categories) where tree is a nested dict of directory
    groups ({'pages': [...], 'children': {dirname: subtree}}) and categories
    maps frontmatter `category` names to top-level pages that declare one.
    """
    global _NAV_CACHE
    if _NAV_CACHE is not None:
        return _NAV_CACHE

    tree = {'pages': [], 'children': {}}
    categories = {}
    for md_path in _discover_doc_files(docs_dir):
        if os.path.basename(md_path) == '404.md':
            continue
        try:
            text = pathlib.Path(md_path).read_text(encoding='utf8')
            front = parse_frontmatter(text)
            title = extract_title(text)
        except Exception:
            front, title = {}, os.path.splitext(os.path.basename(md_path))[0]
        entry = {
            'title': title,
            'href': _doc_html_filename(md_path, docs_dir),
            'order': _nav_page_order(front),
        }
        rel_dir = os.path.relpath(os.path.dirname(md_path), docs_dir)
        if rel_dir == '.':
            category = str(front.get('category', '') or '').strip() if isinstance(front, dict) else ''
            if category:
                categories.setdefault(category, []).append(entry)
            else:
                tree['pages'].append(entry)
        else:
            node = tree
            for part in rel_dir.split(os.sep):
                node = node['children'].setdefault(part, {'pages': [], 'children': {}})
            node['pages'].append(entry)

    _NAV_CACHE = (tree, categories)
    return _NAV_CACHE

def _render_nav_group(dirname, rel_dir, node, docs_dir, active_html, prefix):
    """Render one directory group as a collapsible <details> block."""
    meta = _load_category_meta(os.path.join(docs_dir, rel_dir))
    name = meta.get('name') or dirname.replace('-', ' ').replace('_', ' ').title()
    group_prefix = rel_dir.replace(os.sep, '/') + '/'
    is_open = ' open' if active_html.startswith(group_prefix) else ''

    parts = [f'<li class="nav-group"><details{is_open}><summary>{html_module.escape(str(name))}</summary><ul>']
    for page in _sorted_nav_pages(node['pages']):
        active_class = ' class="active"' if page['href'] == active_html else ''
        parts.append(f'<li><a href="{prefix}{page["href"]}"{active_class}>{html_module.escape(page["title"])}</a></li>')
    for child in _sorted_nav_groups(node['children'], rel_dir, docs_dir):
        parts.append(_render_nav_group(child, os.path.join(rel_dir, child), node['children'][child], docs_dir, active_html, prefix))
    parts.append('</ul></details></li>')
    return '\n'.join(parts)

def _sorted_nav_groups(children, parent_rel, docs_dir):
    """Order sibling directory groups by _category.json `order`, then name."""
    def key(dirname):
        meta = _load_category_meta(os.path.join(docs_dir, parent_rel, dirname) if parent_rel else os.path.join(docs_dir, dirname))
        order = meta.get('order')
        try:
            order = float(order)
        except (TypeError, ValueError):
            order = None
        return (order is None, order or 0, dirname.lower())
    return sorted(children, key=key)

def build_navigation(current_file: str) -> str:
    """Build the sidebar navigation HTML: root pages, frontmatter category
    groups, and nested directory groups with collapsible sections."""
    docs_dir = 'docs'
    active_html = _doc_html_filename(current_file, docs_dir)
    # Links are emitted relative to the current page's depth so they work on
    # any hosting setup, including file:// and zero-config local previews.
    prefix = '../' * active_html.count('/')

    tree, categories = _collect_nav_data(docs_dir)

    nav_html = ['<div class="navigation">']
    nav_html.append('<h2>Documentation</h2>')
    nav_html.append('<ul>')

    # README / Home
    if os.path.exists('README.md'):
        active_class = ' class="active"' if active_html == 'index.html' else ''
        nav_html.append(f'<li><a href="{prefix}index.html"{active_class}>README</a></li>')

    # Uncategorized top-level pages
    for page in _sorted_nav_pages(tree['pages']):
        active_class = ' class="active"' if page['href'] == active_html else ''
        nav_html.append(f'<li><a href="{prefix}{page["href"]}"{active_class}>{html_module.escape(page["title"])}</a></li>')

    # Frontmatter category groups
    for category in sorted(categories, key=str.lower):
        nav_html.append('</ul>')
        nav_html.append(f'<h3 class="nav-category">{html_module.escape(category)}</h3>')
        nav_html.append('<ul>')
        for page in _sorted_nav_pages(categories[category]):
            active_class = ' class="active"' if page['href'] == active_html else ''
            nav_html.append(f'<li><a href="{prefix}{page["href"]}"{active_class}>{html_module.escape(page["title"])}</a></li>')

    # Nested directory groups
    for dirname in _sorted_nav_groups(tree['children'], '', docs_dir):
        nav_html.append(_render_nav_group(dirname, dirname, tree['children'][dirname], docs_dir, active_html, prefix))

    nav_html.append('</ul>')
    nav_html.append('</div>')
    return '\n'.join(nav_html)

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

def _get_image_size(path):
    """Return (width, height) for a local image file, or None on failure."""
    try:
        from PIL import Image
        with Image.open(path) as im:
            return str(im.width), str(im.height)
    except Exception:
        return None

def _resolve_image_source(src, input_path):
    """Resolve an <img src> to a local file path, or None if it is remote/missing."""
    if not src or src.startswith(('http://', 'https://', '//', 'data:', 'mailto:')):
        return None

    candidates = []
    if src.startswith('/'):
        candidates.append(src.lstrip('/'))
    else:
        input_dir = os.path.dirname(input_path) or '.'
        candidates.append(os.path.normpath(os.path.join(input_dir, src)))
        # Also try relative to site root
        candidates.append(src)

    # Try a few likely asset prefixes for sites that use /static or /assets
    prefixed = []
    for path in candidates:
        for prefix in ('static', 'assets'):
            prefixed.append(os.path.join(prefix, path))
    candidates.extend(prefixed)

    seen = set()
    for path in candidates:
        norm = os.path.normpath(path)
        if norm in seen:
            continue
        seen.add(norm)
        if os.path.exists(norm):
            return norm
    return None

def _process_content_images(soup, input_path, output_filename):
    """Copy local content images to output, generate responsive srcset sizes, and add lazy loading."""
    try:
        from PIL import Image
    except ImportError:
        # If Pillow is missing, skip image processing but still add lazy loading attributes
        Image = None

    page_output_dir = os.path.dirname(output_filename)
    source_root = os.getcwd()

    for img in soup.find_all('img'):
        if not img.get('loading'):
            img['loading'] = 'lazy'
        if not img.get('decoding'):
            img['decoding'] = 'async'

        src = img.get('src', '')
        src_path = _resolve_image_source(src, input_path)
        if not src_path:
            continue

        # Determine output destination preserving source directory layout.
        # Images under docs/ map to the site root the same way pages do, so
        # their public URLs mirror the source tree.
        src_rel = os.path.relpath(src_path, source_root)
        docs_prefix = 'docs' + os.sep
        if src_rel.startswith(docs_prefix):
            src_rel = src_rel[len(docs_prefix):]
        output_image_path = os.path.normpath(os.path.join(OUTPUT_DIR, src_rel))
        if not os.path.exists(os.path.dirname(output_image_path)):
            os.makedirs(os.path.dirname(output_image_path), exist_ok=True)

        # Copy the original image to the output tree and update the src attribute
        new_src = os.path.relpath(output_image_path, page_output_dir).replace(os.sep, '/')
        if not os.path.exists(output_image_path) or os.path.getmtime(src_path) > os.path.getmtime(output_image_path):
            shutil.copy2(src_path, output_image_path)
        img['src'] = new_src

        try:
            if Image is None:
                continue
            with Image.open(src_path) as im:
                width, height = im.size
                if 'width' not in img.attrs and 'height' not in img.attrs:
                    img['width'], img['height'] = str(width), str(height)

                # Generate a few standard responsive widths. Always include the original width.
                target_widths = sorted(set([w for w in (480, 800, 1200, 1600) if w < width] + [width]))
                if len(target_widths) <= 1:
                    # Image is small enough that extra sizes don't help
                    continue

                srcset_parts = []
                for w in target_widths:
                    if w == width:
                        entry_rel = new_src
                    else:
                        name, ext = os.path.splitext(output_image_path)
                        scaled_path = f"{name}-{w}w{ext}"
                        entry_rel = os.path.relpath(scaled_path, page_output_dir).replace(os.sep, '/')
                        if not os.path.exists(scaled_path) or os.path.getmtime(src_path) > os.path.getmtime(scaled_path):
                            ratio = w / width
                            h = max(1, int(height * ratio))
                            im_resized = im.resize((w, h), Image.LANCZOS)
                            im_resized.save(scaled_path)
                    srcset_parts.append(f"{entry_rel} {w}w")

                img['srcset'] = ', '.join(srcset_parts)
                img['sizes'] = '(max-width: 900px) 100vw, 900px'
        except Exception as e:
            print(f"Warning: Could not process image {src}: {e}")

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
    
    front_matter = parse_frontmatter(md)
    md = remove_frontmatter(md)

    # Plugin before_convert hooks
    for plugin in _PLUGINS:
        hook = getattr(plugin, 'before_convert', None)
        if callable(hook):
            try:
                result = hook(front_matter, md, input_path, output_filename)
                if isinstance(result, tuple) and len(result) == 2:
                    front_matter, md = result
                elif result is not None:
                    md = str(result)
            except Exception as e:
                print(f"Warning: before_convert hook failed in {plugin.__name__}: {e}")

    # Create a custom link pattern processor
    class LinkRewriter(markdown.treeprocessors.Treeprocessor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Load external link config
            self.config = self.load_config()

        def load_config(self):
            """External link configuration, defaulting when no config.json exists.

            Reads the already-parsed CONFIG rather than re-opening config.json
            off disk -- the old version warned twice per build for every user
            without a config file, which is the documented zero-config path.
            """
            defaults = {
                'open_in_new_tab': True,
                'exclude_domains': [],
                'include_domains': [],
                'exclude_paths': [],
                'attributes': {
                    'rel': 'noopener noreferrer',
                    'class': 'external-link'
                }
            }
            overrides = CONFIG.get('external_links')
            if not isinstance(overrides, dict):
                return defaults
            merged = defaults.copy()
            merged.update(overrides)
            return merged

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

                    # Handle .md extension conversion (including fragment/query variants)
                    base, sep, rest = href.partition('.md')
                    if sep == '.md':
                        suffix = rest
                        if not suffix or suffix.startswith(('#', '?')):
                            href = base + '.html' + suffix

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
    
    # Convert markdown to HTML with link rewriting, GFM features, and plugin extensions
    plugin_extensions = _plugin_markdown_extensions(_PLUGINS)
    html = markdown.markdown(
        md,
        extensions=[
            "fenced_code",
            "codehilite", 
            "nl2br",           # Newlines to <br>
            "sane_lists",     # Better list handling
            "smarty",         # Smart quotes, dashes, etc
            "attr_list",     # {: .class} style attributes
            "def_list",      # Definition lists
            "footnotes",     # [^1] style footnotes
            "md_in_html",    # Markdown inside HTML
            "toc",           # [TOC] generation
            "admonition",    # !!! note style admonitions
            "tables",        # Must be after admonition for nested tables
            LinkRewriterExtension(),
            "wingtip.latex_extension"
        ] + plugin_extensions,
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

    # Optimize content images: copy to output, generate responsive srcset, lazy load
    _process_content_images(soup, input_path, output_filename)

    # Plugin after_convert hooks (operate on fully processed HTML)
    html = str(soup)
    for plugin in _PLUGINS:
        hook = getattr(plugin, 'after_convert', None)
        if callable(hook):
            try:
                result = hook(html, front_matter, input_path, output_filename)
                if isinstance(result, str):
                    html = result
            except Exception as e:
                print(f"Warning: after_convert hook failed in {plugin.__name__}: {e}")
    soup = BeautifulSoup(html, 'html.parser')

    h1 = soup.find('h1')
    title = str(front_matter.get('title') or (h1.text if h1 else os.path.basename(input_path))).strip()

    # Get description from front matter or fallback to first paragraph
    page_description = front_matter.get('description')
    if not page_description:
        p_tag = soup.find('p')
        if p_tag:
            page_description = p_tag.text.strip()
        else:
            page_description = CONFIG.get("description", "")
    # Ensure description doesn't have newlines and is a reasonable length
    page_description = str(page_description).replace('\n', ' ').replace('\r', '')
    if len(page_description) > 160:
        page_description = page_description[:157] + "..."

    # Output path relative to the site root, and a per-page base URL.
    # With a configured base_url every page shares the same absolute base;
    # in zero-config builds (BASE_URL == '.') nested pages need ../ hops so
    # assets and site-level artifacts resolve from any depth.
    rel_out = os.path.relpath(output_filename, OUTPUT_DIR).replace(os.sep, '/')
    page_depth = rel_out.count('/')
    if BASE_URL == '.':
        page_root = '.' if page_depth == 0 else '/'.join(['..'] * page_depth)
    else:
        page_root = BASE_URL

    # Get navigation links
    nav_links = build_navigation(input_path)

    # Build prev/next links (relative to this page's directory)
    prev_link = f'<a href="{_rel_href(rel_out, prev_page[1])}" class="prev">← {prev_page[0]}</a>' if prev_page else ''
    next_link = f'<a href="{_rel_href(rel_out, next_page[1])}" class="next">{next_page[0]} →</a>' if next_page else ''

    # Add edit on GitHub link if requested
    if add_edit_link and CONFIG.get("github", {}).get("repo"):
        repo = CONFIG["github"]["repo"]
        branch = CONFIG["github"].get("branch", "main")
        path = os.path.relpath(input_path)
        edit_url = f"https://github.com/{repo}/edit/{branch}/{path}"
        html += f'\n<p class="edit-link"><a href="{edit_url}">Edit this page on GitHub</a></p>'

    # Canonical URL and page URL (allow per-page override)
    canonical_override = front_matter.get('canonical') or front_matter.get('canonical_url')
    if canonical_override:
        canonical_override = str(canonical_override).strip()
        if canonical_override.startswith(('http://', 'https://')):
            page_url = canonical_url = canonical_override
        else:
            page_url = canonical_url = make_url(canonical_override)
    elif BASE_URL == '.':
        # Zero-config builds have no absolute base; emit a self-resolving
        # relative canonical so the URL is correct at any page depth.
        page_url = canonical_url = f"{page_root}/{rel_out}"
    else:
        page_url = make_url(rel_out)
        canonical_url = page_url

    # Build page using global template
    # Handle favicon URL (support remote, absolute, and relative config values).
    # If the project provides no favicon, emit nothing rather than ship a default logo.
    favicon_config = CONFIG.get('favicon') or ''
    if not favicon_config and os.path.exists(os.path.join(OUTPUT_DIR, 'favicon.png')):
        favicon_config = 'favicon.png'
    favicon_url = resolve_public_url(favicon_config) if favicon_config else ''
    if favicon_url and BASE_URL == '.' and not favicon_url.startswith(('http://', 'https://', '/')):
        favicon_url = f"{page_root}/{favicon_url}"
    if favicon_url:
        favicon_link = f'<link rel="icon" type="image/png" href="{html_module.escape(favicon_url)}">'
        nav_logo = f'<img src="{html_module.escape(favicon_url)}" alt="{html_module.escape(str(CONFIG.get("project_name", title)))}" style="height: 2.5em; vertical-align: middle; margin-right: 0.5em; cursor: pointer;">'
    else:
        favicon_link = ''
        nav_logo = ''

    # Construct URL for the concatenated docs file
    concat_docs_filename = CONFIG.get("concat_docs_filename", "llms-full.txt")
    concat_docs_url = f"{page_root}/{concat_docs_filename}"

    # URL for the RSS feed
    rss_filename = CONFIG.get("rss_filename", "feed.xml")
    feed_url = f"{page_root}/{rss_filename}"

    # PWA asset URLs
    theme_color, _ = get_theme_colors()
    manifest_url = f"{page_root}/manifest.json"
    sw_url = f"{page_root}/sw.js"
    icon_192_url = f"{page_root}/icon-192.png" if os.path.exists(os.path.join(OUTPUT_DIR, 'icon-192.png')) else ''
    icon_512_url = f"{page_root}/icon-512.png" if os.path.exists(os.path.join(OUTPUT_DIR, 'icon-512.png')) else ''
    icon_192_link = f'<link rel="apple-touch-icon" sizes="192x192" href="{icon_192_url}">' if icon_192_url else ''
    icon_512_link = f'<link rel="apple-touch-icon" sizes="512x512" href="{icon_512_url}">' if icon_512_url else ''

    # Custom <head> snippet (analytics, scripts, verification tags, etc.)
    head_snippet = _build_head_snippet(front_matter)

    # Content Security Policy meta tag (optional, disabled by default)
    csp_meta = _build_csp(front_matter)
    if csp_meta:
        csp_meta = f'<meta http-equiv="Content-Security-Policy" content="{html_module.escape(csp_meta, quote=False)}">'
    else:
        csp_meta = ''

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

    # Determine proper OG type and locale (allow frontmatter overrides)
    og_type = front_matter.get('og_type') or front_matter.get('og:type') or ("website" if rel_out == "index.html" else "article")

    # Page-level or site-level language (support `lang` alias)
    language = str(front_matter.get('lang') or front_matter.get('language') or CONFIG.get("language", "en"))
    og_locale = "en_US" if language == "en" else language.replace('-', '_')

    # Hreflang alternate links for multilingual pages
    hreflang_alternates = _build_hreflang_alternates(front_matter, canonical_url)

    # Robots directive: support `noindex: true` and explicit `robots:` frontmatter
    robots = front_matter.get('robots')
    if front_matter.get('noindex') or (isinstance(robots, str) and 'noindex' in robots.lower()):
        robots = robots if isinstance(robots, str) and 'noindex' in robots.lower() else 'noindex, nofollow'
        noindex = True
    else:
        robots = str(robots).strip() if robots else 'index, follow'
        noindex = False

    # Keywords meta
    keywords = front_matter.get('keywords', '')
    if isinstance(keywords, list):
        keywords = ', '.join(str(k).strip() for k in keywords)
    else:
        keywords = str(keywords).strip()

    # Per-page category and version metadata
    category = str(front_matter.get('category', '') or '').strip()
    version = str(front_matter.get('version', '') or '').strip()

    # Per-page OG/Twitter overrides
    og_title = str(front_matter.get('og_title') or front_matter.get('og:title') or title).strip()
    og_description = str(front_matter.get('og_description') or front_matter.get('og:description') or page_description).strip()
    og_image_url = resolve_public_url(
        front_matter.get('og_image') or front_matter.get('og:image') or CONFIG.get('og_image'),
        default='social-card.png'
    )
    twitter_title = str(front_matter.get('twitter_title') or front_matter.get('twitter:title') or og_title).strip()
    twitter_description = str(front_matter.get('twitter_description') or front_matter.get('twitter:description') or og_description).strip()
    twitter_image = front_matter.get('twitter_image') or front_matter.get('twitter:image')
    if twitter_image:
        twitter_image_url = resolve_public_url(twitter_image)
    else:
        twitter_image_url = og_image_url

    author = str(front_matter.get('author') or CONFIG.get("author", "")).strip()

    # Per-page date metadata (date / lastmod frontmatter)
    date_published_raw = front_matter.get('date') or front_matter.get('published')
    date_modified_raw = front_matter.get('lastmod') or front_matter.get('updated')
    lastmod_from_git = get_last_modified(input_path)

    date_published_iso = _iso_date(date_published_raw)
    date_modified_iso = _iso_date(date_modified_raw) or lastmod_from_git

    date_published_display = _display_date(date_published_raw)
    date_modified_display = _display_date(date_modified_raw)

    date_meta_parts = []
    if date_published_display:
        date_meta_parts.append(f'Published {date_published_display}')
    if date_modified_display:
        date_meta_parts.append(f'Updated {date_modified_display}')
    date_meta = f'<p class="page-dates">{" · ".join(date_meta_parts)}</p>' if date_meta_parts else ''

    # Generate JSON-LD Schema
    json_ld_script = ""
    if not noindex:
        tech_article = {
            "@type": "TechArticle",
            "headline": title,
            "description": page_description,
            "dateModified": date_modified_iso,
            "image": og_image_url
        }
        if category:
            tech_article["articleSection"] = category
        if version:
            tech_article["version"] = version
        if date_published_iso:
            tech_article["datePublished"] = date_published_iso

        if author:
            tech_article["author"] = {
                "@type": "Person",
                "name": author
            }

        project_name = CONFIG.get("project_name")
        if project_name:
            tech_article["publisher"] = {
                "@type": "Organization",
                "name": project_name,
                "logo": {
                    "@type": "ImageObject",
                    "url": resolve_public_url(CONFIG.get('favicon', 'favicon.png'))
                }
            }

        breadcrumb_items = [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": BASE_URL
            }
        ]
        if category:
            breadcrumb_items.append({
                "@type": "ListItem",
                "position": 2,
                "name": category,
                "item": page_url
            })
            breadcrumb_items.append({
                "@type": "ListItem",
                "position": 3,
                "name": title,
                "item": page_url
            })
        else:
            breadcrumb_items.append({
                "@type": "ListItem",
                "position": 2,
                "name": title,
                "item": page_url
            })
        json_ld = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "BreadcrumbList",
                    "itemListElement": breadcrumb_items
                },
                tech_article
            ]
        }
        json_ld_script = f'<script type="application/ld+json">\n{json.dumps(json_ld, indent=2)}\n</script>'

    # Properly construct the markdown alternate URL to avoid .md extension applied to the root domain
    markdown_alternate_url = f"{page_root}/{rel_out}.md"

    page = TEMPLATE.substitute(
        title=title,
        canonical_url=canonical_url,
        page_url=page_url,
        keywords=keywords,
        robots=robots,
        date_published=date_published_display,
        last_modified=date_modified_display,
        date_meta=date_meta,
        markdown_url=markdown_alternate_url,
        content=html,
        project=CONFIG.get("project_name") or "Documentation",
        description=page_description,
        language=language,
        og_locale=og_locale,
        og_type=og_type,
        author=author,
        og_title=og_title,
        og_description=og_description,
        og_image_url=og_image_url,
        twitter_title=twitter_title,
        twitter_description=twitter_description,
        twitter_image_url=twitter_image_url,
        twitter_handle=CONFIG.get("twitter_handle", ""),
        version=CONFIG["version"],
        year=datetime.now().year,
        repo_url=CONFIG["repo_url"],
        navigation=nav_links,
        prev_link=prev_link,
        next_link=next_link,
        base_url=page_root,
        favicon_link=favicon_link,
        nav_logo=nav_logo,
        concat_docs_url=concat_docs_url,
        feed_url=feed_url,
        manifest_url=manifest_url,
        sw_url=sw_url,
        theme_color=theme_color,
        icon_192_link=icon_192_link,
        icon_512_link=icon_512_link,
        head_snippet=head_snippet,
        csp_meta=csp_meta,
        hreflang_alternates=hreflang_alternates,
        raw_markdown_content=raw_markdown_for_template,
        custom_theme_variables_style=custom_theme_variables_style,
        json_ld=json_ld_script
    )

    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    with open(output_filename, "w", encoding="utf8") as f:
        f.write(page)

    # Write the markdown sibling file (.html.md)
    if raw_markdown_for_template:
        md_sibling_path = output_filename + ".md"
        with open(md_sibling_path, "w", encoding="utf8") as f:
            f.write(raw_markdown_for_template)

    return front_matter

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

    # Add files from docs/ recursively, excluding 404.md
    for md_path in _discover_doc_files("docs"):
        if os.path.basename(md_path) != "404.md":
            files_to_process.append(md_path)

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

    output_filename = CONFIG.get("concat_docs_filename", "llms-full.txt")
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
    global _NAV_CACHE
    _NAV_CACHE = None
    parser = argparse.ArgumentParser(
        prog="wingtip",
        description=show_help.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  wingtip
  wingtip --serve
  wingtip --source ./docs-project --output ./build
  wingtip --regen-card""",
    )
    parser.add_argument("--regen-card", action="store_true", help="force regeneration of the Open Graph social card")
    parser.add_argument("--output", metavar="DIR", help="output directory (default: docs/site)")
    parser.add_argument("--serve", action="store_true", help="start the live development server after building")
    parser.add_argument("--source", metavar="DIR", help="source project directory (default: current directory)", default=".")
    parser.add_argument("--version", action="version", version=f"%(prog)s {_package_version()}")
    args = parser.parse_args()

    # Update output dir if specified. Resolve it before changing directories so
    # relative output paths are interpreted from the original working directory.
    global OUTPUT_DIR
    if args.output:
        OUTPUT_DIR = os.path.abspath(args.output)
    else:
        OUTPUT_DIR = os.path.abspath(OUTPUT_DIR)

    if args.source != ".":
        os.chdir(args.source)

    # Reload config/theme from the source directory so --source actually uses
    # the target project's configuration, not the tool's checkout defaults.
    global CONFIG, BASE_URL, THEME_CONFIG
    CONFIG = DEFAULT_CONFIG.copy()
    if CFG_PATH.exists():
        try:
            CONFIG.update(json.loads(CFG_PATH.read_text()))
        except Exception as e:
            print(f"Warning: Could not parse config.json: {e}")
    if CONFIG.get("project") and not CONFIG.get("project_name"):
        CONFIG["project_name"] = CONFIG["project"]
    CONFIG["project_name"] = CONFIG.get("project_name") or "Documentation"
    CONFIG["project"] = CONFIG["project_name"]
    BASE_URL = (CONFIG.get("base_url") or ".").rstrip("/") or "."

    THEME_CONFIG = {}
    if THEME_CFG_PATH.exists():
        try:
            THEME_CONFIG = json.loads(THEME_CFG_PATH.read_text())
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse theme.json: {e}. Using default theme.")

    # Without a config.json, derive a project name from the README H1 or the
    # source directory name so unconfigured projects don't inherit a tool brand.
    if not CFG_PATH.exists():
        derived = None
        if os.path.exists("README.md"):
            with open("README.md", "r", encoding="utf8") as f:
                derived = extract_title(remove_frontmatter(f.read()))
        if not derived or derived == "Untitled":
            derived = os.path.basename(os.path.abspath(".")) or "Documentation"
        CONFIG["project_name"] = derived
        CONFIG["project"] = derived
        if not CONFIG.get("description"):
            CONFIG["description"] = f"Documentation for {derived}."

    # Load user plugins before anything is generated
    global _PLUGINS
    _PLUGINS = _load_plugins()
    for plugin in _PLUGINS:
        hook = getattr(plugin, 'before_build', None)
        if callable(hook):
            try:
                hook(CONFIG, OUTPUT_DIR)
            except Exception as e:
                print(f"Warning: before_build hook failed in {plugin.__name__}: {e}")

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
            from .generate_card import generate_social_card
        generate_social_card(
            social.get("title", CONFIG["project_name"]),
            social.get("tagline") or CONFIG.get("tagline") or "",
            theme=social.get("theme", "light"),
            font=social.get("font", "Poppins"),
            logo=social.get("logo"),
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
    sitemap_pages = []
    categories_data = {}
    versions_data = {}

    def _is_noindex(front):
        if not isinstance(front, dict):
            return False
        if front.get('noindex'):
            return True
        robots = front.get('robots')
        if isinstance(robots, str) and 'noindex' in robots.lower():
            return True
        return False
    
    # Start with README if it exists
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf8") as f:
            readme_content_raw = f.read()
        readme_front = parse_frontmatter(readme_content_raw)
        readme_title = extract_title(readme_content_raw)
        readme_md_content_no_frontmatter = remove_frontmatter(readme_content_raw)
        if not _is_noindex(readme_front):
            search_data_for_index.append({
                "title": readme_title,
                "content_md": readme_md_content_no_frontmatter,
                "url": "index.html"
            })
        nav_pages.append((readme_title, "index.html", "README.md", readme_front))
    
    # Then collect all .md files from the docs directory recursively,
    # preserving nested source paths in generated URLs.
    seen_outputs = {"index.html": "README.md"} if nav_pages else {}
    for md_path in _discover_doc_files(docs_dir):
        name = os.path.basename(md_path)
        with open(md_path, "r", encoding="utf8") as f:
            md_content_raw = f.read()
        front = parse_frontmatter(md_content_raw)
        title = extract_title(md_content_raw)
        html_filename = _doc_html_filename(md_path, docs_dir)

        if html_filename in seen_outputs:
            print(f"Warning: {md_path} and {seen_outputs[html_filename]} both map to {html_filename}; skipping {md_path}")
            continue
        seen_outputs[html_filename] = md_path

        if name != "404.md" and not _is_noindex(front):
            md_content_no_frontmatter = remove_frontmatter(md_content_raw)
            category_val = str(front.get('category', '') or '').strip() if isinstance(front, dict) else ''
            version_val = str(front.get('version', '') or '').strip() if isinstance(front, dict) else ''
            search_data_for_index.append({
                "title": title,
                "content_md": md_content_no_frontmatter,
                "url": html_filename,
                "category": category_val,
                "version": version_val
            })
        nav_pages.append((title, html_filename, md_path, front))
    
    # Convert all files with prev/next navigation
    for i, (title, html_file, md_path, front) in enumerate(nav_pages):
        prev_page = nav_pages[i-1][:2] if i > 0 else None
        next_page = nav_pages[i+1][:2] if i < len(nav_pages)-1 else None
        
        output_path = os.path.join(OUTPUT_DIR, html_file)
        front = convert_markdown_file(md_path, output_path, add_edit_link=True,
                            prev_page=prev_page, next_page=next_page)
        pages.append((f"{OUTPUT_DIR}/{html_file}", md_path))
        if not _is_noindex(front) and os.path.basename(output_path) != "404.html":
            sitemap_pages.append((f"{OUTPUT_DIR}/{html_file}", md_path))

    # Generate category and version index files for downstream consumers
    categories_data = {}
    versions_data = {}
    for title, html_file, md_path, front in nav_pages:
        if _is_noindex(front):
            continue
        category_val = str(front.get('category', '') or '').strip() if isinstance(front, dict) else ''
        version_val = str(front.get('version', '') or '').strip() if isinstance(front, dict) else ''
        if category_val:
            categories_data.setdefault(category_val, []).append({"title": title, "url": html_file})
        if version_val:
            versions_data.setdefault(version_val, []).append({"title": title, "url": html_file})

    if categories_data:
        categories_json_path = os.path.join(OUTPUT_DIR, 'categories.json')
        with open(categories_json_path, 'w', encoding='utf8') as f:
            json.dump(categories_data, f, indent=2)
        print(f"Generated categories index: {categories_json_path}")

    if versions_data:
        versions_json_path = os.path.join(OUTPUT_DIR, 'versions.json')
        with open(versions_json_path, 'w', encoding='utf8') as f:
            json.dump(versions_data, f, indent=2)
        print(f"Generated versions index: {versions_json_path}")

    # Process 404.md if it exists
    fourofour_md_path = pathlib.Path("404.md")
    if fourofour_md_path.exists():
        fourofour_html_path = pathlib.Path(OUTPUT_DIR) / "404.html"
        # Title will be extracted by convert_markdown_file from H1 or default to filename
        front = convert_markdown_file(
            input_path=str(fourofour_md_path),
            output_filename=str(fourofour_html_path),
            add_edit_link=False,  # Typically no "edit this page" for a 404
            prev_page=None,
            next_page=None
        )
        pages.append((str(fourofour_html_path), str(fourofour_md_path)))
        
        # For GitHub Pages compatibility, also copy 404.html to the root of the site
        # This ensures it works with the permalink: /404.html front matter

    generate_search_index(search_data_for_index, OUTPUT_DIR)
    write_sitemap_xml(sitemap_pages)
    generate_rss_feed(sitemap_pages, OUTPUT_DIR)
    write_llms_txt(nav_pages)
    write_robots_txt()
    
    # Clean up obsolete files
    cleanup_output_dir([p[0] for p in pages])

    # Generate PWA manifest, icons, offline page, and service worker
    generate_pwa_files(pages, OUTPUT_DIR)

    # Plugin after_build hooks
    for plugin in _PLUGINS:
        hook = getattr(plugin, 'after_build', None)
        if callable(hook):
            try:
                hook(CONFIG, OUTPUT_DIR)
            except Exception as e:
                print(f"Warning: after_build hook failed in {plugin.__name__}: {e}")

    # Start dev server if requested
    if args.serve:
        import subprocess
        import sys
        import time
        from pathlib import Path
        
        serve_script = Path(__file__).parent / "serve.py"
        
        if serve_script.exists():
            print("\nStarting development server...")
            try:
                # First attempt to start the server
                result = subprocess.run([sys.executable, "-m", "wingtip.serve"], capture_output=True, text=True)
                if result.returncode != 0 and "Address already in use" in result.stderr:
                    print("Port 8000 is in use. Please free port 8000 manually.")
                    sys.exit(1)
                elif result.returncode != 0:
                    print(f"\nServer failed to start: {result.stderr}")
                    sys.exit(1)
            except KeyboardInterrupt:
                print("\nServer stopped by user")

if __name__ == "__main__":
    main()
