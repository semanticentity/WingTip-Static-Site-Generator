"""Migrate a hosted documentation project into a WingTip project.

Reads a source project's configuration (docs.json / mint.json) and content,
and writes a NEW WingTip project alongside a scored migration-report.md.

The source project is strictly read-only: nothing under it is created,
modified, or deleted. Diff at leisure.
"""

import argparse
import json
import os
import pathlib
import re
import shutil
import sys

# Configuration formats we can read, in detection order (newest first).
CONFIG_FORMATS = ("docs.json", "mint.json")

# Files and directories never copied from the source project.
SKIP_DIRS = {"node_modules", ".git", ".github", "__pycache__", "site"}
SKIP_FILES = set(CONFIG_FORMATS) | {"package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"}

# Frontmatter keys that carry over to WingTip without changes.
_JSX_COMPONENT = re.compile(r"</?([A-Z][A-Za-z0-9]*)[\s/>]")
_IMPORT_EXPORT = re.compile(r"^(import|export)\s.*$", re.MULTILINE)


def detect_config(source_dir):
    """Return (format_name, path) for the first recognized config file."""
    for name in CONFIG_FORMATS:
        path = os.path.join(source_dir, name)
        if os.path.isfile(path):
            return name, path
    return None, None


def _walk_navigation(value, groups, trail=()):
    """Flatten a navigation tree into ordered (group_trail, page_paths) pairs.

    Handles both flat group lists and container keys (tabs, anchors,
    dropdowns, versions, languages, groups, pages) without assuming a
    specific schema version.
    """
    if isinstance(value, str):
        if trail:
            groups[-1][1].append(value)
        else:
            groups.append((("Pages",), [value]))
        return
    if isinstance(value, list):
        for item in value:
            _walk_navigation(item, groups, trail)
        return
    if not isinstance(value, dict):
        return

    label = value.get("group") or value.get("tab") or value.get("anchor") or value.get("dropdown") or value.get("version") or value.get("language")
    new_trail = trail + (str(label),) if label else trail
    if value.get("group"):
        groups.append((new_trail, []))
        for page in value.get("pages", []):
            if isinstance(page, str):
                groups[-1][1].append(page)
            else:
                _walk_navigation(page, groups, new_trail)
        return
    for key in ("tabs", "anchors", "dropdowns", "versions", "languages", "navigation", "groups", "pages"):
        if key in value:
            _walk_navigation(value[key], groups, new_trail)


def _normalize_page_path(page):
    """Nav page entries are extensionless site paths, possibly with a leading slash."""
    return str(page).strip().lstrip("/")


def _find_page_file(source_dir, page_path):
    """Locate the source file for a nav page path."""
    for ext in (".mdx", ".md"):
        candidate = os.path.join(source_dir, page_path + ext)
        if os.path.isfile(candidate):
            return candidate
    return None


def _convert_mdx(text):
    """Strip module-level import/export lines and inventory JSX components.

    Component markup itself is left in place — it is visible in the page and
    listed in the report as manual work, rather than silently deleted.
    """
    components = sorted(set(_JSX_COMPONENT.findall(text)))
    stripped = _IMPORT_EXPORT.sub("", text)
    stripped = re.sub(r"\n{3,}", "\n\n", stripped)
    return stripped, components


def _patch_frontmatter_order(text, order):
    """Add an `order` key to existing frontmatter, or create frontmatter."""
    match = re.match(r"^---[ \t]*\n(.*?)\n---", text, re.DOTALL)
    if match:
        if re.search(r"^order\s*:", match.group(1), re.MULTILINE):
            return text
        first_newline = text.index("\n")
        return text[: first_newline + 1] + f"order: {order}\n" + text[first_newline + 1 :]
    return f"---\norder: {order}\n---\n\n" + text


def _slugify(name):
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", str(name).lower())
    return slug.strip("-")


_MD_LINK = re.compile(r"(\]\()([^)\s]+)(\))")


def _rewrite_content_links(text, page_key, all_page_keys):
    """Rewrite internal links to point at the migrated .md files.

    Hosted platforms use root-absolute, extensionless page links
    (`/guides/intro`); WingTip resolves ordinary relative Markdown links.
    Every link that resolves to a migrated page becomes a relative .md link
    so WingTip's link rewriter takes it from there.
    """
    page_dir = page_key.rpartition("/")[0]
    is_home = page_key == "index"

    def _replace(match):
        href = match.group(2)
        if href.startswith(("http://", "https://", "mailto:", "#")):
            return match.group(0)
        path, hash_sep, fragment = href.partition("#")
        stripped = path[:-4] if path.endswith(".mdx") else path[:-3] if path.endswith(".md") else path
        if path.startswith("/"):
            key = stripped.lstrip("/")
        else:
            key = os.path.normpath(os.path.join(page_dir, stripped)).replace(os.sep, "/")
        if key not in all_page_keys:
            return match.group(0)
        if is_home:
            # The home page becomes README.md at the project root, where the
            # docs/ prefix convention applies.
            new = "index.md" if key == "index" else f"docs/{key}.md"
        else:
            new = os.path.relpath(key + ".md", page_dir or ".").replace(os.sep, "/")
        return match.group(1) + new + hash_sep + fragment + match.group(3)

    return _MD_LINK.sub(_replace, text)


def migrate(source_dir, output_dir):
    """Run the migration. Returns the report path."""
    source_dir = os.path.abspath(source_dir)
    output_dir = os.path.abspath(output_dir)

    if not os.path.isdir(source_dir):
        raise SystemExit(f"Error: source directory not found: {source_dir}")
    if output_dir == source_dir or output_dir.startswith(source_dir + os.sep):
        raise SystemExit("Error: output directory must be outside the source project (the source is never modified)")
    if os.path.isdir(output_dir) and os.listdir(output_dir):
        raise SystemExit(f"Error: output directory is not empty: {output_dir}")

    fmt, cfg_path = detect_config(source_dir)
    platform_config = {}
    if cfg_path:
        try:
            platform_config = json.loads(pathlib.Path(cfg_path).read_text(encoding="utf8"))
        except Exception as e:
            raise SystemExit(f"Error: could not parse {cfg_path}: {e}")

    docs_out = os.path.join(output_dir, "docs")
    os.makedirs(docs_out, exist_ok=True)

    report = {
        "format": fmt,
        "pages_md": 0,
        "pages_mdx": 0,
        "urls_preserved": [],
        "mdx_components": {},   # rel page -> [components]
        "groups_mapped": [],
        "groups_unmapped": [],
        "orphan_pages": [],
        "redirects": platform_config.get("redirects") or [],
        "config_carried": [],
        "config_not_carried": [],
        "notes": [],
    }

    # ---- Content: copy every doc page, preserving the source tree ----
    nav_groups = []
    _walk_navigation(platform_config.get("navigation"), nav_groups)
    nav_page_order = {}
    order = 0
    for _trail, pages in nav_groups:
        for page in pages:
            nav_page_order[_normalize_page_path(page)] = order
            order += 1

    # Project-level assets are handled separately below, not copied into docs/.
    favicon_rel = str(platform_config.get("favicon") or "").lstrip("/")

    # Pass 1: inventory pages and copy static assets. The full page set is
    # needed before any page is written so internal links can be rewritten.
    page_files = []  # (source path, page key)
    for dirpath, dirnames, filenames in os.walk(source_dir):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name.startswith("."):
                continue
            src = os.path.join(dirpath, name)
            rel = os.path.relpath(src, source_dir)
            stem, ext = os.path.splitext(rel)
            if ext in (".md", ".mdx"):
                page_files.append((src, stem.replace(os.sep, "/"), ext))
            elif name in SKIP_FILES or rel.replace(os.sep, "/") == favicon_rel:
                continue
            else:
                # Static assets keep their positions so relative references hold.
                dest = os.path.join(docs_out, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(src, dest)

    all_page_keys = {key for _, key, _ in page_files}

    # Pass 2: convert and write pages.
    copied_pages = {}  # page key -> output URL
    for src, page_key, ext in page_files:
        text = pathlib.Path(src).read_text(encoding="utf8")
        if ext == ".mdx":
            text, components = _convert_mdx(text)
            report["pages_mdx"] += 1
            if components:
                report["mdx_components"][page_key + ".md"] = components
        else:
            report["pages_md"] += 1
        if page_key in nav_page_order:
            text = _patch_frontmatter_order(text, nav_page_order[page_key])
        else:
            report["orphan_pages"].append(page_key)
        text = _rewrite_content_links(text, page_key, all_page_keys)
        dest = os.path.join(docs_out, page_key.replace("/", os.sep) + ".md")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        pathlib.Path(dest).write_text(text, encoding="utf8")
        copied_pages[page_key] = page_key + ".html"
        report["urls_preserved"].append(page_key + ".html")

    # ---- Home page: index at the source root becomes README.md ----
    index_src = copied_pages.get("index")
    if index_src == "index.html":
        shutil.move(os.path.join(docs_out, "index.md"), os.path.join(output_dir, "README.md"))
        report["notes"].append("Root `index` page became `README.md` (site home).")
    else:
        title = platform_config.get("name") or os.path.basename(source_dir)
        pathlib.Path(os.path.join(output_dir, "README.md")).write_text(
            f"# {title}\n\nDocumentation home. (Generated during migration — the source project had no root `index` page; replace with your own introduction.)\n",
            encoding="utf8",
        )
        report["notes"].append("No root `index` page found; generated a stub `README.md` to serve as the site home.")

    # ---- Navigation groups -> _category.json where they align with directories ----
    group_index = 0
    for trail, pages in nav_groups:
        if not pages or not trail:
            continue
        group_name = trail[-1]
        # A group maps cleanly when every page shares a common ancestor
        # directory (subdirectories are fine — nested nav renders them).
        # The root `index` page is exempt: it becomes the site home.
        page_dirs = []
        mappable = True
        for p in pages:
            norm = _normalize_page_path(p)
            if norm == "index":
                continue
            d = norm.rpartition("/")[0]
            if not d:
                mappable = False
                break
            page_dirs.append(d)
        target_dir = os.path.commonpath(page_dirs).replace(os.sep, "/") if (mappable and page_dirs) else ""
        if target_dir:
            cat_path = os.path.join(docs_out, target_dir, "_category.json")
            if os.path.isdir(os.path.dirname(cat_path)) and not os.path.exists(cat_path):
                pathlib.Path(cat_path).write_text(
                    json.dumps({"name": group_name, "order": group_index}, indent=2) + "\n",
                    encoding="utf8",
                )
                report["groups_mapped"].append((group_name, target_dir))
                group_index += 1
                continue
        report["groups_unmapped"].append(group_name)

    # ---- Site config and theme ----
    wingtip_config = {}
    if platform_config.get("name"):
        wingtip_config["project_name"] = str(platform_config["name"])
        report["config_carried"].append("name → project_name")
    if platform_config.get("description"):
        wingtip_config["description"] = str(platform_config["description"])
        report["config_carried"].append("description")
    if wingtip_config:
        pathlib.Path(os.path.join(output_dir, "config.json")).write_text(
            json.dumps(wingtip_config, indent=2) + "\n", encoding="utf8"
        )

    colors = platform_config.get("colors") or {}
    if colors.get("primary"):
        theme = {
            "light_mode": {"links_or_primary": colors["primary"]},
            "dark_mode": {"links_or_primary": colors.get("light") or colors["primary"]},
        }
        pathlib.Path(os.path.join(output_dir, "theme.json")).write_text(
            json.dumps(theme, indent=2) + "\n", encoding="utf8"
        )
        report["config_carried"].append("colors → theme.json")

    favicon = platform_config.get("favicon")
    if favicon:
        fav_src = os.path.join(source_dir, str(favicon).lstrip("/"))
        if os.path.isfile(fav_src):
            if fav_src.lower().endswith(".png"):
                shutil.copy2(fav_src, os.path.join(output_dir, "favicon.png"))
                report["config_carried"].append("favicon")
            else:
                shutil.copy2(fav_src, os.path.join(output_dir, os.path.basename(fav_src)))
                report["notes"].append(
                    f"Favicon `{favicon}` copied, but WingTip needs a PNG (`favicon.png`) for favicon and PWA icons — convert it."
                )

    handled_keys = {"name", "description", "colors", "favicon", "navigation", "redirects", "$schema", "theme"}
    report["config_not_carried"] = sorted(k for k in platform_config if k not in handled_keys)

    report_path = _write_report(output_dir, report)
    return report_path


def _write_report(output_dir, r):
    total_pages = r["pages_md"] + r["pages_mdx"]
    manual = len(r["mdx_components"]) + (1 if r["redirects"] else 0) + len(r["config_not_carried"]) + len(r["groups_unmapped"])

    lines = []
    lines.append("# Migration Report")
    lines.append("")
    lines.append("> Your original project was **not modified**. This directory is a new, independent WingTip project — diff at leisure.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    detected = f"`{r['format']}` configuration" if r["format"] else "no recognized configuration file (content-only migration)"
    lines.append(f"- **Detected:** {detected}")
    lines.append(f"- **Pages converted:** {total_pages} ({r['pages_mdx']} `.mdx` → `.md`, {r['pages_md']} `.md`)")
    lines.append(f"- **URLs preserved:** {len(r['urls_preserved'])} of {total_pages}")
    lines.append(f"- **Navigation groups mapped:** {len(r['groups_mapped'])} mapped, {len(r['groups_unmapped'])} need review")
    lines.append(f"- **Manual follow-ups:** {manual}")
    lines.append("")

    lines.append("## Converted")
    lines.append("")
    for name, target in r["groups_mapped"]:
        lines.append(f"- ✓ Group **{name}** → `docs/{target}/_category.json`")
    if r["urls_preserved"]:
        lines.append(f"- ✓ {len(r['urls_preserved'])} page URLs preserved (nested paths kept intact)")
    for item in r["config_carried"]:
        lines.append(f"- ✓ Config: {item}")
    for note in r["notes"]:
        lines.append(f"- ✓ {note}")
    lines.append("")

    if r["mdx_components"] or r["redirects"] or r["config_not_carried"] or r["groups_unmapped"] or r["orphan_pages"]:
        lines.append("## Needs manual work")
        lines.append("")
        if r["mdx_components"]:
            lines.append(f"### Custom components ({len(r['mdx_components'])} pages)")
            lines.append("")
            lines.append("These pages use JSX components that have no direct Markdown equivalent. The markup was left in place so nothing is silently lost — rewrite each as Markdown (admonitions, tables, and plain HTML cover most cases):")
            lines.append("")
            for page, comps in sorted(r["mdx_components"].items()):
                lines.append(f"- ⚠ `docs/{page}`: {', '.join(f'`<{c}>`' for c in comps)}")
            lines.append("")
        if r["groups_unmapped"]:
            lines.append("### Navigation groups needing review")
            lines.append("")
            lines.append("These groups span multiple directories (or none), so WingTip's directory-based navigation can't mirror them automatically. Pages keep their nav order via `order` frontmatter; regroup by moving files or adding `_category.json` files:")
            lines.append("")
            for name in r["groups_unmapped"]:
                lines.append(f"- ⚠ {name}")
            lines.append("")
        if r["orphan_pages"]:
            lines.append("### Pages not in the source navigation")
            lines.append("")
            lines.append("Copied, but they were not listed in the source navigation (they will appear in WingTip's sidebar via their directory):")
            lines.append("")
            for page in sorted(r["orphan_pages"]):
                lines.append(f"- ⚠ `docs/{page}.md`")
            lines.append("")
        if r["redirects"]:
            lines.append(f"### Redirects ({len(r['redirects'])})")
            lines.append("")
            lines.append("WingTip generates static files; redirects are host-level configuration (e.g. `_redirects` on Netlify/Cloudflare, `vercel.json` rewrites):")
            lines.append("")
            for rd in r["redirects"]:
                src = rd.get("source", "?") if isinstance(rd, dict) else str(rd)
                dst = rd.get("destination", "?") if isinstance(rd, dict) else ""
                lines.append(f"- ⚠ `{src}` → `{dst}`")
            lines.append("")
        if r["config_not_carried"]:
            lines.append("### Configuration not carried over")
            lines.append("")
            for key in r["config_not_carried"]:
                lines.append(f"- ⚠ `{key}`")
            lines.append("")

    lines.append("## Next steps")
    lines.append("")
    lines.append("1. `cd` into this directory and run `wingtip --serve` to preview the site")
    lines.append("2. Set `base_url` in `config.json` to your production URL before deploying")
    lines.append("3. Work through the manual items above, rebuilding as you go")
    lines.append("4. Deploy `docs/site/` to any static host")
    lines.append("")

    report_path = os.path.join(output_dir, "migration-report.md")
    pathlib.Path(report_path).write_text("\n".join(lines), encoding="utf8")
    return report_path


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="wingtip migrate",
        description="Migrate a hosted documentation project into a new WingTip project. The source is read-only; output includes a migration-report.md.",
    )
    parser.add_argument("source", help="path to the existing documentation project")
    parser.add_argument("--output", metavar="DIR", help="directory for the new WingTip project (default: <source>-wingtip)")
    args = parser.parse_args(argv)

    output = args.output or (os.path.abspath(args.source).rstrip(os.sep) + "-wingtip")
    report_path = migrate(args.source, output)

    print(f"Migrated project written to: {output}")
    print(f"Migration report: {report_path}")
    print(f"\nNext: cd {output} && wingtip --serve")


if __name__ == "__main__":
    main()
