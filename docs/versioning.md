# Document Versioning

WingTip includes support for building and browsing multiple versions of your documentation. This is useful if your project has different releases with varying features, APIs, or user guides.

## Strategy Overview

The versioning system works by:
1.  Storing Markdown source files for each version in separate subdirectories.
2.  Using a build script (`build_all_versions.py`) to iterate through these versions.
3.  Calling the main `main.py` script for each version with specific input, output, and versioning parameters.
4.  Generating versioned output paths (e.g., `docs/site/v1.0/`, `docs/site/v0.9/`).
5.  Providing a version selector dropdown in the documentation UI to switch between versions.
6.  Creating a redirect from the site root to the "latest" specified version.

## Directory Structure

Organize your Markdown source files as follows:

```
your-project/
├── docs_src_versions/        # Parent directory for all versioned sources
│   ├── v1.0/                 # Source files for version 1.0
│   │   ├── README.md
│   │   ├── feature-x.md
│   │   └── ...
│   ├── v0.9/                 # Source files for version 0.9
│   │   ├── README.md
│   │   ├── old-feature.md
│   │   └── ...
│   └── ...                   # Other versions
├── docs/site/                # Default main output directory (parent for versioned sites)
│   ├── v1.0/                 # Output for version 1.0
│   │   ├── index.html
│   │   ├── feature-x.html
│   │   └── ...
│   ├── v0.9/                 # Output for version 0.9
│   │   └── ...
│   └── index.html            # Redirects to the latest version (e.g., ./v1.0/)
├── plugins/
├── static/
├── build_all_versions.py     # Script to build all versions
├── main.py                   # Core WingTip script
├── config.json
└── requirements.txt
```

- **`docs_src_versions/`**: This directory (configurable in `build_all_versions.py`) holds the source Markdown files for each distinct version of your documentation. Each subdirectory within it (e.g., `v1.0`, `v0.9`) represents a single version.
- **`docs/site/`**: This is the typical output directory. When versioning is used, `build_all_versions.py` will instruct `main.py` to place each version's generated HTML site into a subdirectory here (e.g., `docs/site/v1.0/`).

## `build_all_versions.py`

This script, located in your project root, automates the building of all defined documentation versions.

Key aspects:
- **Version Definition:** Versions are typically defined by the subdirectories found in `VERSION_SOURCE_PARENT_DIR` (e.g., `docs_src_versions/`). The script can be modified to explicitly list versions (e.g., `PREDEFINED_VERSIONS = ["v1.0", "v0.9"]`).
- **Iteration:** It loops through each identified version.
- **Calling `main.py`:** For each version, it executes `main.py` using `subprocess.run()`, passing necessary command-line arguments:
    - `--input_dir`: Set to the version's source directory (e.g., `docs_src_versions/v1.0`).
    - `--output_dir`: Set to the main site output parent (e.g., `docs/site`). `main.py` will then create a subdirectory for the version (e.g., `docs/site/v1.0`).
    - `--version_string`: The current version being built (e.g., `v1.0`).
    - `--all_versions_json`: A JSON string representing the list of all available versions (e.g., `'["v1.0", "v0.9"]'`). This is used to populate the version selector.
- **"Latest" Version Redirect:** After building all versions, the script determines the "latest" version (usually by simple sorting, e.g., `v1.0` is later than `v0.9`). It then creates an `index.html` file in the root of the main site output directory (`docs/site/index.html`) that contains an HTML meta redirect to the latest version's `index.html` (e.g., redirects to `./v1.0/`).

**Example `build_all_versions.py` snippet:**
```python
# (Simplified from actual script)
import subprocess
import os
import json

VERSION_SOURCE_PARENT_DIR = "docs_src_versions"
SITE_OUTPUT_PARENT_DIR = "docs/site"
PREDEFINED_VERSIONS = ["v1.0", "v0.9"] # Or discover from subdirectories
LATEST_VERSION_STR = sorted(PREDEFINED_VERSIONS, reverse=True)[0]

all_versions_json_string = json.dumps(PREDEFINED_VERSIONS)

for version_str in PREDEFINED_VERSIONS:
    input_dir = os.path.join(VERSION_SOURCE_PARENT_DIR, version_str)
    # main.py handles creating output_dir/version_str

    command = [
        "python", "main.py",
        "--input_dir", input_dir,
        "--output_dir", SITE_OUTPUT_PARENT_DIR,
        "--version_string", version_str,
        "--all_versions_json", all_versions_json_string
    ]
    subprocess.run(command, check=True)

# Create latest redirect (details omitted for brevity)
# ...
```

## `main.py` CLI Arguments for Versioning

The `main.py` script uses the following arguments when building a specific version:
-   `--input_dir <path>`: Specifies the source directory for the Markdown files of the version being built (e.g., `docs_src_versions/v1.0`).
-   `--output_dir <path>`: Specifies the *base* output directory (e.g., `docs/site`). `main.py` will create a subdirectory named after `--version_string` within this base directory (e.g., `docs/site/v1.0`).
-   `--version_string <string>`: The version identifier (e.g., `v1.0`). This is used in URL paths and for display.
-   `--all_versions_json <json_string>`: A JSON formatted string array of all available version strings (e.g., `'["v1.0", "v0.9", "latest"]'`). This populates the version selector.

## Version Selector UI

If `current_version` and `all_versions` are available in the template context (passed from `main.py`):
- A dropdown `<select>` menu is rendered in the site's navigation bar.
- It lists all versions found in `all_versions_json`.
- The currently viewed version is pre-selected.
- Selecting a different version from the dropdown navigates the user to the `index.html` of that selected version (e.g., `https://yoursite.com/base_path/v0.9/`).

The HTML for the selector is generated dynamically in `main.py` and injected into the template.

## How "Latest" Version is Handled

The `build_all_versions.py` script creates a simple `index.html` file at the root of your `SITE_OUTPUT_PARENT_DIR` (e.g., `docs/site/index.html`). This file contains a meta refresh tag that redirects users to the subdirectory of the most recent version. For example, if `v1.0` is the latest, accessing `https://yoursite.com/` would redirect to `https://yoursite.com/v1.0/`.

This ensures that users landing on the root URL are always directed to the most up-to-date documentation by default. The `all_versions` list passed to `main.py` can also include a "latest" entry, which the version selector logic in `main.py` can map to the root URL or the specific latest version URL.

## Example Usage

1.  **Structure your documents:**
    ```
    docs_src_versions/
        v1.0/
            README.md
            page1.md
        v0.9/
            README.md
            page1.md
    ```
2.  **Configure `build_all_versions.py`**:
    - Set `VERSION_SOURCE_PARENT_DIR = "docs_src_versions"`.
    - Ensure `PREDEFINED_VERSIONS` list matches your directory names (or implement dynamic discovery).
3.  **Run the build script:**
    ```bash
    python build_all_versions.py
    ```
4.  **Serve the site:**
    The main `serve.py` typically serves from `docs/site`. Accessing `http://localhost:8000/` should redirect to `http://localhost:8000/v1.0/` (if v1.0 is latest). You can then navigate to `http://localhost:8000/v0.9/`, etc.
```
