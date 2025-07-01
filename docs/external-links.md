# External Link Handling

WingTip provides flexible control over how external links (links to other websites) are handled in your documentation.

## Configuration

External link behavior is controlled through the `external_links` section in your `config.json`:

```json
{
    "external_links": {
        "open_in_new_tab": true,
        "exclude_domains": ["example.com", "mycompany.com"],
        "include_domains": ["external-docs.example.com"],
        "exclude_paths": ["/docs/internal/*"],
        "attributes": {
            "rel": "noopener noreferrer",
            "class": "external-link"
        }
    }
}
```

### Options

* `open_in_new_tab` (boolean): Global setting that determines if external links should open in a new tab by default.
* `exclude_domains` (array): List of domains that should NOT open in a new tab, even if `open_in_new_tab` is true.
* `include_domains` (array): List of domains that should ALWAYS open in a new tab, regardless of other settings.
* `exclude_paths` (array): URL path patterns (using glob syntax) that should NOT open in a new tab.
* `attributes` (object): Additional HTML attributes to add to external links:
  * `rel`: Relationship attributes (default: "noopener noreferrer" for security)
  * `class`: CSS class to apply to external links (default: "external-link")

## Examples

### Basic Configuration

The simplest configuration is to make all external links open in new tabs:

```json
{
    "external_links": {
        "open_in_new_tab": true
    }
}
```

### Selective Control

You can exempt certain domains from opening in new tabs while keeping the default behavior for others:

```json
{
    "external_links": {
        "open_in_new_tab": true,
        "exclude_domains": ["trusted-site.com", "internal-docs.com"]
    }
}
```

Or force specific domains to always open in new tabs while leaving others as regular links:

```json
{
    "external_links": {
        "open_in_new_tab": false,
        "include_domains": ["external-api-docs.com", "github.com"]
    }
}
```

### Path-Based Control

You can use path patterns to control behavior for specific URL paths:

```json
{
    "external_links": {
        "open_in_new_tab": true,
        "exclude_paths": [
            "/docs/internal/*",
            "*/preview/*"
        ]
    }
}
```

### Custom Attributes

Add custom attributes to external links for styling or tracking:

```json
{
    "external_links": {
        "open_in_new_tab": true,
        "attributes": {
            "rel": "noopener noreferrer",
            "class": "external-link branded",
            "data-track": "external-click"
        }
    }
}
```

## Default Behavior

If no configuration is provided, WingTip will:

1. Open external links in new tabs
2. Add `rel="noopener noreferrer"` for security
3. Add `class="external-link"` for styling

## Styling External Links

The default `external-link` class allows you to style external links differently. For example, in your custom CSS:

```css
.external-link {
    /* Add an external link indicator */
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>');
    background-position: right 3px center;
    background-repeat: no-repeat;
    background-size: 12px;
    padding-right: 20px;
}
```

This will add a small external link icon to visually indicate links that open in new tabs.
