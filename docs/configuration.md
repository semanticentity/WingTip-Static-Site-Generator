# Configuration

WingTip can be customized through a `config.json` file in your project root.

## Example Config

```json
{
    "project": "Your Project",
    "description": "A brief description of your project",
    "github": {
        "repo": "username/repo",
        "branch": "main"
    },
    "social": {
        "title": "Custom social card title",
        "tagline": "Custom social card tagline",
        "theme": "light",
        "font": "Poppins"
    }
}
```

## Options

### Basic Settings
- `project` - Your project name (shown in navigation)
- `description` - Project description (used in meta tags)

### GitHub Integration
- `github.repo` - Repository path (e.g., "username/repo")
- `github.branch` - Branch name for "Edit this page" links

### Social Card Settings
- `social.title` - Title for the social preview card
- `social.tagline` - Subtitle for the social preview card
- `social.theme` - Card theme ("light" or "dark")
- `social.font` - Font for card text (defaults to "Poppins")

## Social Cards

WingTip automatically generates beautiful social preview cards for your documentation:

1. **Default Card**
   - Uses your project name and description
   - Generated when you build the site

2. **Custom Card**
   - Configure via `social` settings in config.json
   - Supports custom title/tagline
   - Choose light/dark theme
   - Select custom Google Font

### Card Examples

```json
{
    "social": {
        "title": "WingTip Docs",
        "tagline": "Beautiful documentation in minutes",
        "theme": "light",
        "font": "Poppins"
    }
}
```

### Font Support
- Uses Google Fonts API
- Automatically downloads and caches fonts
- Falls back to system fonts if download fails
- Recommended: "Poppins", "Inter", "Roboto"

### Card Location
- Generated in `docs/site/social-card.png`
- Automatically used by GitHub, Twitter, etc.
- 1200x630px with optimized text layout
