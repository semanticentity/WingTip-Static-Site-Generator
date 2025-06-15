import subprocess
import os
import json
import shutil

# Configuration
# Define source directories for different versions of the documentation
# Assumes each version's docs are in a subdirectory under 'docs_src_versions'
# e.g., docs_src_versions/v1.0, docs_src_versions/v0.9
VERSION_SOURCE_PARENT_DIR = "docs_src_versions"

# Define the base output directory for all versioned sites
SITE_OUTPUT_PARENT_DIR = "docs/site"

# List of version strings to build. These should match subdirectory names in VERSION_SOURCE_PARENT_DIR.
# Example: VERSIONS_TO_BUILD = ["v2.0", "v1.5", "v1.0"]
# For auto-discovery, you could scan VERSION_SOURCE_PARENT_DIR:
# VERSIONS_TO_BUILD = [d for d in os.listdir(VERSION_SOURCE_PARENT_DIR)
#                      if os.path.isdir(os.path.join(VERSION_SOURCE_PARENT_DIR, d)) and d.startswith('v')]
# For this task, let's predefine them.
# We need to create these dummy source directories for the script to run without error.
PREDEFINED_VERSIONS = ["v1.0", "v0.9"]

# Determine the "latest" version (e.g., highest version number)
# This is a simple sort; more complex logic might be needed for semantic versioning with pre-releases etc.
LATEST_VERSION_STR = sorted(PREDEFINED_VERSIONS, reverse=True)[0] if PREDEFINED_VERSIONS else None

def create_dummy_version_dirs():
    """Creates dummy source version directories and files for testing."""
    print("Creating dummy version directories and files...")
    for version_str in PREDEFINED_VERSIONS:
        version_input_dir = os.path.join(VERSION_SOURCE_PARENT_DIR, version_str)
        os.makedirs(version_input_dir, exist_ok=True)

        # Create a dummy README.md
        with open(os.path.join(version_input_dir, "README.md"), "w") as f:
            f.write(f"# README for {version_str}\n\nThis is content for {version_str}.")
        # Create a dummy subpage.md
        with open(os.path.join(version_input_dir, "subpage.md"), "w") as f:
            f.write(f"# Subpage for {version_str}\n\nDetails for {version_str} subpage.")
    print("Dummy directories and files created.")

def main():
    # Create dummy dirs first for the script to work in the sandbox
    create_dummy_version_dirs()

    versions_available_for_selector = PREDEFINED_VERSIONS.copy()
    # Optionally, add a "latest" entry that points to the root or a specific version
    # If LATEST_VERSION_STR is to be redirected from site root,
    # main.py needs to handle version_string=None for root build.
    # For now, all_versions_json will just be the list of actual version numbers.
    # The template can have a separate static link to "/" for "latest" if needed,
    # or we can add "latest" to all_versions_json and handle its URL in main.py template logic.

    all_versions_json_string = json.dumps(versions_available_for_selector)

    # Ensure the main site output directory exists
    os.makedirs(SITE_OUTPUT_PARENT_DIR, exist_ok=True)

    for version_str in PREDEFINED_VERSIONS:
        input_dir = os.path.join(VERSION_SOURCE_PARENT_DIR, version_str)
        output_dir = os.path.join(SITE_OUTPUT_PARENT_DIR, version_str)

        print(f"\nBuilding version: {version_str}")
        print(f"  Input directory: {input_dir}")
        print(f"  Output directory: {output_dir}")

        command = [
            "python",
            "main.py",
            "--input_dir", input_dir,
            "--output_dir", SITE_OUTPUT_PARENT_DIR, # Pass the parent, main.py will append version_str
            "--version_string", version_str,
            "--all_versions_json", all_versions_json_string
            # Add other global options if needed, e.g., --regen-card
        ]

        try:
            process = subprocess.run(command, check=True, capture_output=True, text=True)
            print(f"Successfully built version {version_str}.")
            if process.stdout:
                print("Output:\n", process.stdout)
            if process.stderr:
                print("Errors/Warnings:\n", process.stderr)
        except subprocess.CalledProcessError as e:
            print(f"Error building version {version_str}:")
            print("Command:", e.cmd)
            print("Return code:", e.returncode)
            print("Output (stdout):\n", e.stdout)
            print("Output (stderr):\n", e.stderr)
            # Decide if you want to stop on error or continue with other versions
            # For now, it stops.
            return
        except FileNotFoundError:
            print(f"Error: main.py not found. Make sure it's in the same directory or in PATH.")
            return

    # Create/update a symlink or redirect for "latest" version
    # This part is OS-dependent for symlinks (Windows needs admin or different command)
    # A simple redirect HTML file is more portable for static sites.
    if LATEST_VERSION_STR:
        latest_redirect_path = os.path.join(SITE_OUTPUT_PARENT_DIR, "index.html")
        try:
            # Create an HTML redirect file in the root of SITE_OUTPUT_PARENT_DIR
            # This redirects SITE_OUTPUT_PARENT_DIR/index.html to SITE_OUTPUT_PARENT_DIR/LATEST_VERSION_STR/
            redirect_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta http-equiv="refresh" content="0; url=./{LATEST_VERSION_STR}/" />
    <title>Redirecting to latest version</title>
    <link rel="canonical" href="./{LATEST_VERSION_STR}/" />
</head>
<body>
    <p>Redirecting to the <a href="./{LATEST_VERSION_STR}/">latest version ({LATEST_VERSION_STR})</a>.</p>
</body>
</html>'''
            with open(latest_redirect_path, "w", encoding="utf8") as f:
                f.write(redirect_content)
            print(f"\nCreated/Updated 'latest' redirect at {latest_redirect_path} to point to ./{LATEST_VERSION_STR}/")

            # Also consider if a root README is needed (e.g. from a non-versioned main input_dir)
            # This script currently only builds versioned docs.
            # A separate call to main.py without --version_string could build the root.
            # Example:
            # print("\nBuilding root/non-versioned documentation (if any)...")
            # subprocess.run(["python", "main.py", "--input_dir", "docs_root_src", "--output_dir", SITE_OUTPUT_PARENT_DIR, "--all_versions_json", all_versions_json_string])


        except Exception as e:
            print(f"Warning: Could not create 'latest' redirect at {latest_redirect_path}: {e}")
            print("  You might need to create it manually, e.g., an index.html that redirects,")
            print(f"  or configure your web server to redirect / to /{LATEST_VERSION_STR}/.")

    print("\nAll specified versions built.")

if __name__ == "__main__":
    main()
