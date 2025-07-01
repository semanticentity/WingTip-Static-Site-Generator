# Admonition Examples

WingTip supports admonition blocks to highlight important information. These are special callout blocks that can be used to draw attention to specific content.

## Basic Usage

Use `!!!` followed by the type of admonition to create a block:

!!! note
    This is a simple note admonition.
    It can contain multiple paragraphs and other Markdown elements.

    - Lists
    - Code blocks
    - etc.

## Available Types

### Note
!!! note
    This is a note admonition. Use it for general information.

### Warning
!!! warning
    This is a warning admonition. Use it to warn users about potential issues.

### Danger
!!! danger
    This is a danger admonition. Use it for critical warnings or dangerous operations.

### Tip
!!! tip
    This is a tip admonition. Use it for helpful suggestions and best practices.

### Info
!!! info
    This is an info admonition. Use it for additional context or background information.

### Success
!!! success
    This is a success admonition. Use it to highlight positive outcomes or completion states.

## Advanced Usage

### Nested Content

Admonitions can contain any Markdown content:

!!! note
    ### A Header Inside an Admonition

    1. Ordered lists work great
    2. Code blocks work too:

    ```python
    def hello():
        print("Hello from an admonition!")
    ```

    Tables work when not nested in lists:

    | Column 1 | Column 2 |
    |----------|----------|
    | Cell 1   | Cell 2   |

### Custom Titles

You can add custom titles to admonitions:

!!! tip "Custom Title"
    This tip has a custom title!

## Dark Mode Support

All admonitions automatically adapt to dark mode when the theme is switched, maintaining readability and consistent styling with the rest of the content.
