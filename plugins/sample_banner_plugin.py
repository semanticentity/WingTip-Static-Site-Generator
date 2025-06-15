# plugins/sample_banner_plugin.py

def after_full_page_assembly(final_html, metadata, output_filepath):
    """
    Adds a "Beta Site" banner at the top of the <body> of every generated page.
    """
    banner_html = "<div style='background-color: yellow; color: black; text-align: center; padding: 5px; border-bottom: 1px solid black;'>Beta Preview - Content may change!</div>"

    # Ensure we are dealing with a string
    if not isinstance(final_html, str):
        # This case should ideally not happen if main.py passes string
        return final_html

    # Try to insert after <body> tag
    body_tag_index = final_html.lower().find("<body")
    if body_tag_index != -1:
        # Find where the body tag actually ends (e.g., <body class="foo">)
        end_of_body_tag_index = final_html.find(">", body_tag_index)
        if end_of_body_tag_index != -1:
            final_html = final_html[:end_of_body_tag_index + 1] + banner_html + final_html[end_of_body_tag_index + 1:]
        else:
            # Fallback: append after the found "<body" part if no ">" (should be unlikely for valid HTML)
            # This might mess up attributes if any, but it's a fallback.
            final_html = final_html[:body_tag_index + len("<body>")] + banner_html + final_html[body_tag_index + len("<body>"):]
    else:
        # Fallback if no <body> tag is found (e.g., partial HTML snippet)
        # Prepend to the whole content. This is less ideal.
        final_html = banner_html + final_html

    return final_html

def before_markdown_conversion(md_content, metadata, filepath):
    """
    Example hook: Adds a prefix to markdown content if a certain metadata key is present.
    """
    if metadata.get("add_markdown_prefix"):
        prefix = metadata.get("add_markdown_prefix")
        md_content = f"{prefix}\n\n{md_content}"
        print(f"Plugin: Added prefix to {filepath} from metadata.")
    return md_content, metadata

def after_html_generation(html_content, metadata, filepath):
    """
    Example hook: Replaces a placeholder in the HTML body if metadata key exists.
    """
    if "replace_placeholder_text" in metadata:
        placeholder = "<!-- REPLACE_WITH_METADATA -->"
        replacement = metadata["replace_placeholder_text"]
        html_content = html_content.replace(placeholder, replacement)
        print(f"Plugin: Replaced placeholder in {filepath} from metadata.")
    return html_content
