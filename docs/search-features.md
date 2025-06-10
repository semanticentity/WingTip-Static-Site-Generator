# Client-Side Search Functionality

WingTip includes a powerful and lightweight client-side search feature that allows users to quickly find relevant information within the documentation.

## How it Works

The search functionality is designed to be fast and entirely client-side, making it suitable for static hosting environments like GitHub Pages. Here's a brief overview:

1.  **Search Index (`search_index.json`)**: When the site is built, WingTip generates a file named `search_index.json`. This file contains a structured list of all the pages in your documentation (excluding special pages like 404). For each page, the index stores:
    *   The page title.
    *   The plain text content of the page (with HTML tags and frontmatter removed).
    *   The relative URL to the page.

2.  **Client-Side Processing**: When a user types into the search bar:
    *   The browser fetches the `search_index.json` file (this happens only once, on the first search interaction typically).
    *   JavaScript running in the browser then filters this index based on the search query.
    *   It matches the query against both the titles and the text content of the pages.
    *   Matching results are displayed dynamically below the search bar as a list of links.

## Using the Search Bar

-   The search bar is located in the main navigation header for easy access.
-   Simply type your search terms into the input field.
-   Results will appear as you type (minimum 2 characters required).
-   Clicking on a search result will take you directly to the relevant page.

## Benefits

-   **Fast**: Since the search happens in the user's browser with a local index, it's very responsive.
-   **No Server-Side Dependencies**: Works perfectly on static hosting platforms.
-   **Comprehensive**: Searches both page titles and full text content.

This approach ensures that your documentation remains easy to navigate and user-friendly without requiring complex backend infrastructure.
