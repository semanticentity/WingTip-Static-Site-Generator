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


# Component approximations: callout tags become admonitions, titled
# sections become bold labels, layout wrappers are dropped (their content
# stands on its own in linear Markdown).
ADMONITION_TAGS = {"Note": "note", "Warning": "warning", "Tip": "tip", "Info": "info", "Check": "success"}
TITLE_TAGS = {"Step", "Tab", "Accordion", "Expandable", "ParamField", "ResponseField"}
DROP_TAGS = {"Frame", "Steps", "Tabs", "CardGroup", "AccordionGroup", "CodeGroup", "Columns", "Col", "Tooltip", "Icon"}

_TAG_ATTR = re.compile(r'(\w+)=(?:"([^"]*)"|\'([^\']*)\')')
_FENCE = re.compile(r"^\s*(```|~~~)")


def _tag_attrs(tag_text):
    return {m.group(1): (m.group(2) if m.group(2) is not None else m.group(3)) for m in _TAG_ATTR.finditer(tag_text)}


def _convert_mdx(text):
    """Convert MDX to renderable Markdown.

    - Strips module-level import/export lines.
    - Approximates common components: callouts -> admonitions, titled
      sections (Step/Tab/Accordion) -> bold labels, Card -> a link,
      pure layout wrappers dropped.
    - Removes JSX nesting indentation outside code fences (Markdown would
      read 4+ leading spaces as an indented code block; MDX has no indented
      code blocks, so this is safe for .mdx sources).
    - Inventories any component that was NOT cleanly approximated.

    Returns (converted_text, unhandled_components, approximated_components).
    """
    text = _IMPORT_EXPORT.sub("", text)
    # MDX comments ({/* ... */}) are never rendered; drop them entirely.
    text = re.sub(r"\{/\*.*?\*/\}", "", text, flags=re.DOTALL)
    approximated = set()
    lines = []
    fence_open = None  # indent width of the opening fence line, else None

    # Join JSX tags that span multiple lines (multi-attribute components are
    # usually written one attribute per line) so the whole-line handling
    # below sees them. Fence-aware: code samples are left alone.
    joined = []
    pending = None
    fence_state = False
    for raw in text.split("\n"):
        if _FENCE.match(raw):
            fence_state = not fence_state
        if pending is not None:
            pending += " " + raw.strip()
            if ">" in raw:
                joined.append(pending)
                pending = None
            continue
        stripped = raw.strip()
        if not fence_state and re.match(r"^<[A-Za-z][A-Za-z0-9]*(\s|$)", stripped) and ">" not in stripped:
            pending = raw.rstrip()
            continue
        joined.append(raw)
    if pending is not None:
        joined.append(pending)

    for raw in joined:
        if fence_open is not None:
            # Inside a fence: remove the fence's own indentation, keep
            # relative indentation of its content.
            lines.append(raw[fence_open:] if raw[:fence_open].strip() == "" else raw)
            if _FENCE.match(raw):
                fence_open = None
            continue
        fence_match = _FENCE.match(raw)
        if fence_match:
            fence_open = len(raw) - len(raw.lstrip())
            lines.append(raw.lstrip())
            continue

        line = raw
        stripped = line.strip()

        # Standalone raw <img> lines become Markdown images: raw HTML blocks
        # interact badly with list/block parsing (they can be swallowed into
        # code blocks or escaped), while Markdown images parse reliably in
        # any context.
        m = re.match(r"^<img\s([^>]*?)/?>$", stripped, re.IGNORECASE)
        if m:
            attrs = _tag_attrs(m.group(1))
            if attrs.get("src"):
                lines.append(f"![{attrs.get('alt', '')}]({attrs['src']})")
                continue

        # Whole-line component tags
        m = re.match(r"^</?([A-Z][A-Za-z0-9]*)([^>]*?)/?>$", stripped)
        if m:
            name, rest = m.group(1), m.group(2)
            closing = stripped.startswith("</")
            if name in DROP_TAGS:
                approximated.add(name)
                lines.append("")
                continue
            if name in ADMONITION_TAGS and not closing:
                approximated.add(name)
                lines.append(f"\x00ADMON\x00{ADMONITION_TAGS[name]}")
                continue
            if name in ADMONITION_TAGS and closing:
                lines.append("\x00ENDADMON\x00")
                continue
            if name in TITLE_TAGS:
                approximated.add(name)
                if closing:
                    lines.append("")
                else:
                    title = _tag_attrs(rest).get("title") or _tag_attrs(rest).get("name") or ""
                    lines.append(f"**{title}**" if title else "")
                continue
            if name == "Card":
                approximated.add(name)
                if closing:
                    lines.append("")
                else:
                    attrs = _tag_attrs(rest)
                    title, href = attrs.get("title", ""), attrs.get("href", "")
                    if title and href:
                        lines.append(f"[**{title}**]({href})")
                    elif title:
                        lines.append(f"**{title}**")
                    else:
                        lines.append("")
                continue
            # Any other leaf component carrying a src attribute is
            # approximated as an image (linked if it also has an href) so
            # the referenced asset renders and gets copied into the build.
            if not closing and stripped.endswith("/>"):
                attrs = _tag_attrs(rest)
                if attrs.get("src"):
                    approximated.add(name)
                    img = f"![{attrs.get('alt', '')}]({attrs['src']})"
                    lines.append(f"[{img}]({attrs['href']})" if attrs.get("href") else img)
                    continue
        # Inline single-line callout: <Note>text</Note>
        m = re.match(r"^<([A-Z][A-Za-z0-9]*)>(.*)</\1>$", stripped)
        if m and m.group(1) in ADMONITION_TAGS:
            approximated.add(m.group(1))
            lines.append(f"\x00ADMON\x00{ADMONITION_TAGS[m.group(1)]}")
            lines.append(m.group(2).strip())
            lines.append("\x00ENDADMON\x00")
            continue
        lines.append(line)

    # Dedent JSX nesting outside fences, block by block, preserving
    # relative indentation (nested lists survive).
    dedented = []
    block = []
    fence_state = False

    def _flush(block):
        if not block:
            return
        indents = [len(l) - len(l.lstrip()) for l in block if l.strip()]
        cut = min(indents) if indents else 0
        if cut >= 2:
            dedented.extend(l[cut:] if l.strip() else "" for l in block)
        else:
            dedented.extend(block)

    for line in lines:
        if _FENCE.match(line):
            fence_state = not fence_state
            _flush(block)
            block = []
            dedented.append(line)
            continue
        if fence_state:
            dedented.append(line)
            continue
        if not line.strip():
            _flush(block)
            block = []
            dedented.append(line)
        else:
            block.append(line)
    _flush(block)

    # Assemble callout regions as blockquotes. Blockquotes have no
    # indentation semantics, so raw HTML and images inside a callout can't
    # accidentally become indented code blocks. Callouts containing fenced
    # code degrade to a bold label instead (quoted fences don't parse).
    final = []
    admon_stack = []  # (label, body_lines)

    def _flush_admon(target):
        label, body = admon_stack.pop()
        while body and not body[0].strip():
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()
        if any(_FENCE.match(b) for b in body):
            target.append(f"**{label.title()}:**")
            target.append("")
            target.extend(body)
        else:
            target.append(f"> **{label.title()}**")
            target.append(">")
            target.extend("> " + b if b.strip() else ">" for b in body)
        target.append("")

    for line in dedented:
        if line.startswith("\x00ADMON\x00"):
            admon_stack.append((line.split(chr(0))[2], []))
        elif line == "\x00ENDADMON\x00" and admon_stack:
            _flush_admon(admon_stack[-1][1] if len(admon_stack) > 1 else final)
        elif admon_stack:
            admon_stack[-1][1].append(line)
        else:
            final.append(line)
    while admon_stack:
        _flush_admon(admon_stack[-1][1] if len(admon_stack) > 1 else final)

    result = re.sub(r"\n{3,}", "\n\n", "\n".join(final))
    unhandled = sorted(set(_JSX_COMPONENT.findall(result)))
    return result, unhandled, sorted(approximated)


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
_ATTR_LINK = re.compile(r"((?:href|src)=)([\"'])([^\"']*)\2")
_ATTR_EXPR = re.compile(r"(?:href|src)=\{([^}]+)\}")
_SKIP_SCHEMES = ("http://", "https://", "mailto:", "tel:", "data:", "#")


def _resolve_internal(href, page_dir, pages, assets, pages_lower=None, assets_lower=None):
    """Resolve an internal href to ('page'|'asset', key) or (None, None).

    Tries the path relative to the current page first, then as a site-root
    path — hosted platforms use both, often without a leading slash or file
    extension because their router resolves them. A case-insensitive
    fallback covers platforms that route case-insensitively; the canonical
    on-disk casing is returned so links survive case-sensitive hosts.
    """
    path = href.lstrip("/") if href.startswith("/") else href
    stripped = path[:-4] if path.endswith(".mdx") else path[:-3] if path.endswith(".md") else path
    candidates = []
    if not href.startswith("/") and page_dir:
        candidates.append(os.path.normpath(os.path.join(page_dir, stripped)).replace(os.sep, "/"))
    candidates.append(os.path.normpath(stripped).replace(os.sep, "/") if stripped else "index")
    for key in candidates:
        if key in ("", "."):
            key = "index"
        if key in pages:
            return "page", key
        if pages_lower and key.lower() in pages_lower:
            return "page", pages_lower[key.lower()]
    # Asset candidates keep their extension.
    asset_candidates = []
    if not href.startswith("/") and page_dir:
        asset_candidates.append(os.path.normpath(os.path.join(page_dir, path)).replace(os.sep, "/"))
    asset_candidates.append(os.path.normpath(path).replace(os.sep, "/"))
    for key in asset_candidates:
        if key in assets:
            return "asset", key
        if assets_lower and key.lower() in assets_lower:
            return "asset", assets_lower[key.lower()]
    return None, None


def _rewrite_content_links(text, page_key, pages, assets, report, pages_lower=None, assets_lower=None):
    """Rewrite internal links — Markdown links and raw href/src attributes —
    to portable relative paths in the migrated tree.

    Page links in Markdown become relative .md links (WingTip's pipeline
    converts those); page links in raw attributes become relative .html
    links (raw markup bypasses that pipeline). Brace-expression targets
    (`href={variable}`) are stubbed to '#' and reported — the variable only
    exists in the platform's JavaScript. Unresolvable internal links are
    reported as suspected broken links in the source.
    """
    page_dir = page_key.rpartition("/")[0]
    is_home = page_key == "index"

    def _target(href, as_markdown):
        """Return replacement href, or None to leave unchanged."""
        if not href or href.startswith(_SKIP_SCHEMES):
            return None
        # Any URL scheme (cursor:, vscode:, slack:, ...) is external.
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", href):
            return None
        if "{" in href:
            report["expression_links"].setdefault(page_key, []).append(href)
            return "#"
        path, hash_sep, fragment = href.partition("#")
        kind, key = _resolve_internal(path, page_dir, pages, assets, pages_lower, assets_lower)
        if kind == "page":
            if as_markdown:
                new = ("index.md" if key == "index" else f"docs/{key}.md") if is_home \
                    else os.path.relpath(key + ".md", page_dir or ".").replace(os.sep, "/")
            else:
                # Raw markup is not rewritten by the build pipeline; link
                # straight to the generated page.
                new = os.path.relpath(key + ".html", page_dir or ".").replace(os.sep, "/")
            return new + hash_sep + fragment
        if kind == "asset":
            # Assets live in the docs/ tree; the home page (README.md at the
            # project root) reaches them through the docs/ prefix.
            new = f"docs/{key}" if is_home else os.path.relpath(key, page_dir or ".").replace(os.sep, "/")
            return new + hash_sep + fragment
        if path.startswith("/"):
            report["broken_links"].setdefault(page_key, []).append(href)
        return None

    def _md_replace(match):
        new = _target(match.group(2), as_markdown=True)
        return match.group(0) if new is None else match.group(1) + new + match.group(3)

    def _attr_replace(match):
        new = _target(match.group(3), as_markdown=False)
        return match.group(0) if new is None else match.group(1) + match.group(2) + new + match.group(2)

    def _expr_replace(match):
        report["expression_links"].setdefault(page_key, []).append(match.group(1).strip())
        return 'href="#"'

    text = _MD_LINK.sub(_md_replace, text)
    text = _ATTR_LINK.sub(_attr_replace, text)
    text = _ATTR_EXPR.sub(_expr_replace, text)
    return text


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
        "components_approximated": {},  # component name -> page count
        "expression_links": {},  # page -> [expressions]
        "broken_links": {},      # page -> [unresolvable internal hrefs]
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

    # Pass 1: inventory pages and copy static assets. The full page and
    # asset sets are needed before any page is written so internal links
    # can be rewritten.
    page_files = []  # (source path, page key)
    asset_keys = set()
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
                asset_keys.add(rel.replace(os.sep, "/"))

    all_page_keys = {key for _, key, _ in page_files}
    pages_lower = {k.lower(): k for k in all_page_keys}
    assets_lower = {k.lower(): k for k in asset_keys}

    # Pass 2: convert and write pages.
    copied_pages = {}  # page key -> output URL
    for src, page_key, ext in page_files:
        text = pathlib.Path(src).read_text(encoding="utf8")
        if ext == ".mdx":
            text, components, approximated = _convert_mdx(text)
            report["pages_mdx"] += 1
            if components:
                report["mdx_components"][page_key + ".md"] = components
            for name in approximated:
                report["components_approximated"][name] = report["components_approximated"].get(name, 0) + 1
        else:
            report["pages_md"] += 1
        if page_key in nav_page_order:
            text = _patch_frontmatter_order(text, nav_page_order[page_key])
        else:
            report["orphan_pages"].append(page_key)
        text = _rewrite_content_links(text, page_key, all_page_keys, asset_keys, report, pages_lower, assets_lower)
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

    _write_agents_md(output_dir, platform_config.get("name") or os.path.basename(source_dir))
    report["notes"].append("`AGENTS.md` written — docs-maintenance instructions any coding agent can follow (build, verify, add pages, preserve URLs).")

    report_path = _write_report(output_dir, report)
    return report_path


def _write_agents_md(output_dir, project_name):
    """Emit AGENTS.md: a docs-maintenance skill for coding agents.

    The migrated project carries its own maintenance instructions, so any
    agent the team already uses (not a hosted platform's) can keep the
    docs healthy: build, verify, add pages, preserve URLs.
    """
    content = f"""# AGENTS.md — maintaining the {project_name} documentation

This project is a [WingTip](https://pypi.org/project/wingtip/) documentation site.
Source of truth is Markdown in this repository; the generated site is `docs/site/`.

## Build and verify

```bash
pip install wingtip
wingtip                 # build -> docs/site/
wingtip --serve         # build + live-reload preview
```

A healthy build prints no warnings. Treat any `Warning:` line as a task.

## Adding a page

1. Create `docs/<section>/<slug>.md`. The URL mirrors the path:
   `docs/guides/intro.md` → `guides/intro.html`.
2. Start with frontmatter:

   ```yaml
   ---
   title: Page title
   description: One-sentence summary used for search and social previews.
   order: 3            # position within its sidebar group (lower = higher)
   ---
   ```

3. Rebuild. The page appears in the sidebar, search index, sitemap,
   llms.txt, and feed automatically.

## Rules that keep the site healthy

- **Never rename or move a published page path** — URLs are the public
  contract. If a move is unavoidable, add a redirect at the host.
- Link between pages with relative Markdown links to the `.md` file
  (`[intro](../guides/intro.md)`); WingTip rewrites them at build time.
- Reference images relative to the page; WingTip copies them and
  generates responsive variants.
- Name sidebar groups with `docs/<dir>/_category.json`:
  `{{"name": "Guides", "order": 1}}`.
- Frontmatter `noindex: true` hides a page from search engines, search,
  sitemap, and feeds while keeping it reachable by URL.
- Dates: `date:` (published) and `lastmod:` feed the feed and JSON-LD.

## After a migration

`migration-report.md` lists outstanding manual work (custom components,
suspected broken links, redirects). Work through its ⚠ items and delete
each from the report as it lands; the report is done when only ✓ remain.

## Definition of done

`wingtip` builds without warnings and every changed page renders
correctly in `wingtip --serve`.
"""
    pathlib.Path(os.path.join(output_dir, "AGENTS.md")).write_text(content, encoding="utf8")


def _write_report(output_dir, r):
    total_pages = r["pages_md"] + r["pages_mdx"]
    manual = (
        len(r["mdx_components"])
        + len(r["expression_links"])
        + len(r["broken_links"])
        + (1 if r["redirects"] else 0)
        + len(r["config_not_carried"])
        + len(r["groups_unmapped"])
    )

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
    if r["components_approximated"]:
        summary = ", ".join(f"`<{name}>` ({count})" for name, count in sorted(r["components_approximated"].items()))
        lines.append(f"- ✓ Components approximated as Markdown: {summary}")
    for item in r["config_carried"]:
        lines.append(f"- ✓ Config: {item}")
    for note in r["notes"]:
        lines.append(f"- ✓ {note}")
    lines.append("")

    if r["mdx_components"] or r["redirects"] or r["config_not_carried"] or r["groups_unmapped"] or r["orphan_pages"] or r["expression_links"] or r["broken_links"]:
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
        if r["expression_links"]:
            lines.append(f"### Dynamic link expressions ({len(r['expression_links'])} pages)")
            lines.append("")
            lines.append("These links used JavaScript expressions (`href={variable}`) that only exist in the source platform's runtime. They were stubbed to `#` — replace each with a real URL:")
            lines.append("")
            for page, exprs in sorted(r["expression_links"].items()):
                lines.append(f"- ⚠ `docs/{page}.md`: {', '.join(f'`{e}`' for e in sorted(set(exprs)))}")
            lines.append("")
        if r["broken_links"]:
            lines.append(f"### Suspected broken links in the source ({len(r['broken_links'])} pages)")
            lines.append("")
            lines.append("These internal links did not resolve to any page or asset in the source project — they were likely already broken before migration. Left unchanged for review:")
            lines.append("")
            for page, hrefs in sorted(r["broken_links"].items()):
                lines.append(f"- ⚠ `docs/{page}.md`: {', '.join(f'`{h}`' for h in sorted(set(hrefs)))}")
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
