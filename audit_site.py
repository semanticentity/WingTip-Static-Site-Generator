#!/usr/bin/env python3
"""Post-build auditor for WingTip sites.

Runs after `wingtip` and fails the build if:
- any local asset referenced by an HTML file is missing
- any page references a known CDN origin for assets WingTip now vendors
- required PWA / SEO files are absent
"""

import argparse
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

# CDN origins that WingTip now vendors locally. Any reference in generated HTML
# means the vendoring/template did not take effect.
CDN_ORIGINS = {
    "cdn.jsdelivr.net",
    "unpkg.com",
    "cdnjs.cloudflare.com",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "code.iconify.design",
}

REQUIRED_FILES = [
    "favicon.png",
    "icon-192.png",
    "icon-512.png",
    "manifest.json",
    "sw.js",
    "offline.html",
    "llms.txt",
    "llms-full.txt",
    "feed.xml",
    "sitemap.xml",
    "robots.txt",
    "search_index.json",
]


def main():
    parser = argparse.ArgumentParser(description="Audit a WingTip build output")
    parser.add_argument("-o", "--output", required=True, help="Path to the generated site directory")
    args = parser.parse_args()

    site = Path(args.output).resolve()
    if not site.is_dir():
        print(f"FAIL: output directory does not exist: {site}", file=sys.stderr)
        sys.exit(1)

    errors = []
    warnings = []

    # Required files
    for name in REQUIRED_FILES:
        path = site / name
        if not path.exists():
            errors.append(f"Missing required file: {name}")

    # Scan HTML
    for html in site.rglob("*.html"):
        text = html.read_text(encoding="utf8")
        rel_base = html.parent.relative_to(site) if html.parent != site else Path(".")

        # Find all href / src / url() references
        urls = set()
        for m in re.finditer(r'(?:href|src)=["\']([^"\']+)["\']', text):
            urls.add(m.group(1))
        for m in re.finditer(r'url\\(([^)]+)\\)', text):
            urls.add(m.group(1).strip('"\''))

        for url in urls:
            parsed = urlparse(url)

            # External / CDN check
            if parsed.scheme in ("http", "https"):
                origin = parsed.netloc.lower().lstrip("www.")
                # Strip port if present
                origin = origin.split(":")[0]
                if origin in CDN_ORIGINS:
                    errors.append(f"{html.relative_to(site)} references CDN {url}")
                continue

            # Skip non-document anchors, data URIs, mailto, etc.
            if not url or url.startswith(("#", "data:", "mailto:", "tel:", "javascript:")):
                continue

            # Resolve local reference. Treat leading / as site-root relative,
            # otherwise relative to the HTML file.
            if url.startswith("/"):
                target = site / url.lstrip("/")
            else:
                target = (html.parent / url).resolve()
                try:
                    target.relative_to(site)
                except ValueError:
                    warnings.append(
                        f"{html.relative_to(site)} references file outside site: {url}"
                    )
                    continue

            # Drop fragment/query for filesystem check
            target_path = str(target).split("#")[0].split("?")[0]
            if not Path(target_path).exists():
                errors.append(
                    f"{html.relative_to(site)} references missing file: {url}"
                )

    if warnings:
        for w in warnings:
            print(f"WARN: {w}", file=sys.stderr)

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)

    print("Audit passed: no missing local files and no CDN origins.")


if __name__ == "__main__":
    main()
