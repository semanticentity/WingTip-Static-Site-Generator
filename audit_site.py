#!/usr/bin/env python3
"""Post-build auditor for WingTip sites.

Runs after `wingtip` and fails the build if:
- any local asset referenced by an HTML file is missing
- any page references a known CDN origin for assets WingTip now vendors
- required PWA / SEO files are absent
- the site ships a packaged/default WingTip asset byte-for-byte
- the site contains WingTip branding when the project is not WingTip
"""

import argparse
import hashlib
import importlib.resources
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

# Files every build must produce, regardless of project configuration.
REQUIRED_FILES = [
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

# Extensions we consider for byte-identical packaged-asset checks.
BRANDING_EXTENSIONS = {".png", ".jpg", ".jpeg", ".ico", ".svg", ".woff", ".woff2", ".ttf", ".otf", ".eot"}


def _package_static_dir():
    """Return the path to the packaged `wingtip/static` directory, or None."""
    try:
        return importlib.resources.files("wingtip") / "static"
    except Exception:
        return None


def _hash_file(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)
    except Exception:
        return None
    return h.hexdigest()


def _packaged_asset_hashes():
    """Map relative asset path to SHA256 for files in the package static tree."""
    pkg = _package_static_dir()
    if pkg is None or not pkg.is_dir():
        return {}
    hashes = {}
    for path in pkg.rglob("*"):
        if path.is_file() and path.suffix.lower() in BRANDING_EXTENSIONS:
            rel = str(path.relative_to(pkg)).replace(os.sep, "/")
            hashes[rel] = _hash_file(path)
    return hashes


def _branding_check(site, project_name, errors):
    """Ensure no generated asset is a byte-for-byte copy of a packaged asset."""
    pkg_hashes = _packaged_asset_hashes()
    if not pkg_hashes:
        return

    vendor_dir = site / "static" / "vendor"
    # Build an index of output file hashes, keyed by hash.
    # Files under static/vendor are the vendored dependencies themselves,
    # so they legitimately match the packaged assets.
    output_hashes = {}
    for path in site.rglob("*"):
        if path.is_file() and path.suffix.lower() in BRANDING_EXTENSIONS:
            try:
                if vendor_dir in path.parents:
                    continue
            except TypeError:
                pass
            h = _hash_file(path)
            if h:
                output_hashes.setdefault(h, []).append(path)

    for rel, pkg_hash in pkg_hashes.items():
        for leaked in output_hashes.get(pkg_hash, []):
            errors.append(
                f"{leaked.relative_to(site)} is byte-identical to packaged asset {rel}"
            )

    # If the project is not WingTip, no generated page should contain the
    # WingTip brand string (the tool should not name itself in the user's site).
    if project_name and project_name.lower() != "wingtip":
        for html in site.rglob("*.html"):
            text = html.read_text(encoding="utf8")
            if "WingTip" in text:
                errors.append(
                    f"{html.relative_to(site)} contains WingTip branding but project_name is '{project_name}'"
                )


def main():
    parser = argparse.ArgumentParser(description="Audit a WingTip build output")
    parser.add_argument("-o", "--output", required=True, help="Path to the generated site directory")
    parser.add_argument("-p", "--project-name", default="", help="Project name from config.json")
    parser.add_argument("-s", "--source", default="", help="Path to the source directory (to read config.json)")
    args = parser.parse_args()

    site = Path(args.output).resolve()
    if not site.is_dir():
        print(f"FAIL: output directory does not exist: {site}", file=sys.stderr)
        sys.exit(1)

    project_name = args.project_name
    source_dir = Path(args.source).resolve() if args.source else None
    if not project_name and source_dir:
        config_path = source_dir / "config.json"
        if config_path.exists():
            try:
                import json
                cfg = json.loads(config_path.read_text(encoding="utf8"))
                project_name = cfg.get("project_name") or cfg.get("project", "")
            except Exception:
                pass

    errors = []
    warnings = []

    # Required files
    for name in REQUIRED_FILES:
        path = site / name
        if not path.exists():
            errors.append(f"Missing required file: {name}")

    # If the project supplied a favicon, the PWA icons must exist.
    if (site / "favicon.png").exists():
        for name in ("icon-192.png", "icon-512.png"):
            if not (site / name).exists():
                errors.append(f"favicon.png exists but {name} is missing")

    # Scan HTML. Parse rather than regex: only href/src attributes on real
    # elements are fetchable references — attribute-shaped text inside code
    # samples or the raw-markdown embed is not.
    from bs4 import BeautifulSoup

    try:
        import lxml  # noqa: F401
        parser = "lxml"
    except ImportError:
        parser = "html.parser"

    # Navigation links repeat on every page; memoize per-(page-dir, url)
    # verdicts so a large site costs one check per unique target instead
    # of pages x links. Verdict: None = fine, str = error message suffix.
    resolution_cache = {}

    for html in site.rglob("*.html"):
        text = html.read_text(encoding="utf8")
        # lxml drops content appended after </html>; strip the closers so
        # trailing markup (a corruption the audit must catch) is parsed too.
        soup = BeautifulSoup(re.sub(r"</(?:body|html)>", "", text, flags=re.I), parser)

        # Remove non-rendered regions up front (linear), so the attribute
        # scan below never sees code samples or embedded raw markdown.
        for region in soup.find_all(["pre", "code", "template", "textarea"]):
            region.decompose()

        urls = set()
        for el in soup.find_all(href=True):
            urls.add(el["href"])
        for el in soup.find_all(src=True):
            urls.add(el["src"])

        for url in urls:
            cache_key = (html.parent, url)
            if cache_key in resolution_cache:
                verdict = resolution_cache[cache_key]
                if verdict:
                    errors.append(f"{html.relative_to(site)} {verdict}")
                continue

            verdict = None
            parsed = urlparse(url)

            # External / CDN check
            if parsed.scheme in ("http", "https"):
                origin = parsed.netloc.lower().lstrip("www.")
                origin = origin.split(":")[0]
                if origin in CDN_ORIGINS:
                    verdict = f"references CDN {url}"
            elif parsed.scheme:
                # Any other scheme (mailto:, tel:, cursor:, vscode:, data:,
                # javascript:, ...) is not a local file reference.
                pass
            elif not url or url.startswith("#"):
                # Fragment-only anchor.
                pass
            else:
                # Resolve local reference. Treat leading / as site-root
                # relative, otherwise relative to the HTML file.
                if url.startswith("/"):
                    target = site / url.lstrip("/")
                    outside = False
                else:
                    target = (html.parent / url).resolve()
                    outside = False
                    try:
                        target.relative_to(site)
                    except ValueError:
                        outside = True
                        warnings.append(
                            f"{html.relative_to(site)} references file outside site: {url}"
                        )
                if not outside:
                    # Drop fragment/query for filesystem check
                    target_path = str(target).split("#")[0].split("?")[0]
                    if not Path(target_path).exists():
                        verdict = f"references missing file: {url}"

            resolution_cache[cache_key] = verdict
            if verdict:
                errors.append(f"{html.relative_to(site)} {verdict}")

    _branding_check(site, project_name, errors)

    if warnings:
        for w in warnings:
            print(f"WARN: {w}", file=sys.stderr)

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)

    print("Audit passed: no missing local files, no CDN origins, and no branding leaks.")


if __name__ == "__main__":
    main()
