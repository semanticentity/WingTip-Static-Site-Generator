document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('search-input');
  const resultsContainer = document.getElementById('search-results-container');
  const searchClearBtn = document.getElementById('search-clear-btn');
  let searchIndex = [];
  let activeResultIndex = -1;

  if (resultsContainer && searchInput && searchInput.value.trim().length >= 2) {
    resultsContainer.innerHTML = '<p>Loading search...</p>';
    resultsContainer.style.display = 'block';
  } else if (resultsContainer) {
    resultsContainer.style.display = 'none';
  }

  const searchIndexPath = (window.SITE_BASE_URL && window.SITE_BASE_URL !== '.' ? window.SITE_BASE_URL : '') + '/search_index.json';
  fetch(searchIndexPath)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok for search_index.json');
      }
      return response.json();
    })
    .then(data => {
      searchIndex = data;
      if (searchInput.value.trim().length < 2 && resultsContainer) {
        resultsContainer.style.display = 'none';
        resultsContainer.innerHTML = '';
      } else if (searchInput.value.trim().length >= 2 && resultsContainer && resultsContainer.innerHTML.includes("Loading search...")) {
        searchInput.dispatchEvent(new Event('input', { bubbles: true }));
      }
    })
    .catch(error => {
      console.error('Error fetching or parsing search_index.json:', error);
      if (resultsContainer) {
        resultsContainer.innerHTML = '<p style="color: red;">Error loading search data. Please try again later.</p>';
        resultsContainer.style.display = 'block';
      }
    });

  if (searchInput && resultsContainer) {
    function escapeRegExp(string) {
      return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // $& means the whole matched string
    }

    function highlightText(text, query) {
      if (!query || !text) return text;
      const escapedQuery = escapeRegExp(query);
      const regex = new RegExp(escapedQuery, 'gi');
      return text.replace(regex, (match) => '<mark>' + match + '</mark>');
    }

    searchInput.addEventListener('input', () => {
      const originalQuery = searchInput.value.trim();
      const lowerCaseQuery = originalQuery.toLowerCase();

      if (searchClearBtn) {
        if (originalQuery.length > 0) {
          searchClearBtn.style.display = 'inline';
        } else {
          searchClearBtn.style.display = 'none';
        }
      }

      activeResultIndex = -1;
      resultsContainer.innerHTML = '';

      if (lowerCaseQuery.length < 2) {
        resultsContainer.style.display = 'none';
        return;
      }

      const results = searchIndex.filter(item => {
        const titleMatch = item.title && item.title.toLowerCase().includes(lowerCaseQuery);
        const textMatch = item.text && item.text.toLowerCase().includes(lowerCaseQuery);
        return titleMatch || textMatch;
      });

      resultsContainer.style.display = 'block';

      if (results.length > 0) {
        const ul = document.createElement('ul');
        ul.style.listStyleType = 'none';
        ul.style.padding = '0';
        ul.style.margin = '0';
        results.forEach(item => {
          const li = document.createElement('li');
          const a = document.createElement('a');
          a.href = item.url;

          const titleElement = document.createElement('div');
          titleElement.className = 'search-result-title';
          titleElement.innerHTML = highlightText(item.title, originalQuery);
          a.appendChild(titleElement);
          li.appendChild(a);

          if (item.text) {
            let snippetText = '';
            const queryIndex = item.text.toLowerCase().indexOf(lowerCaseQuery);
            const snippetLength = 150;

            if (queryIndex !== -1) {
              const queryActualLength = originalQuery.length;
              let start = Math.max(0, queryIndex - Math.floor((snippetLength - queryActualLength) / 2));
              let end = Math.min(item.text.length, start + snippetLength);

              if (end - start < snippetLength && start === 0) {
                end = Math.min(item.text.length, snippetLength);
              }
              if (end - start < snippetLength && end === item.text.length) {
                start = Math.max(0, item.text.length - snippetLength);
              }

              snippetText = item.text.substring(start, end);
              if (start > 0) snippetText = '...' + snippetText;
              if (end < item.text.length) snippetText = snippetText + '...';

            } else {
              snippetText = item.text.substring(0, snippetLength) + (item.text.length > snippetLength ? '...' : '');
            }

            if (snippetText) {
              const snippetElement = document.createElement('p');
              snippetElement.className = 'search-result-snippet';
              snippetElement.innerHTML = highlightText(snippetText, originalQuery);
              li.appendChild(snippetElement);
            }
          }
          ul.appendChild(li);
        });
        resultsContainer.appendChild(ul);
      } else {
        resultsContainer.innerHTML = '<p>No results found. Try different keywords or check your spelling.</p>';
      }
    });

    if (searchClearBtn) {
      searchClearBtn.addEventListener('click', () => {
        searchInput.value = '';
        searchClearBtn.style.display = 'none';
        resultsContainer.innerHTML = '';
        resultsContainer.style.display = 'none';
        activeResultIndex = -1;
        searchInput.focus();
      });
    }

    searchInput.addEventListener('keydown', (event) => {
      const resultItems = resultsContainer.querySelectorAll('ul li');

      if (resultsContainer.style.display === 'none' || !resultItems || resultItems.length === 0) {
        activeResultIndex = -1;
        return;
      }

      if (event.key === 'ArrowDown') {
        event.preventDefault();
        if (activeResultIndex >= 0 && activeResultIndex < resultItems.length) {
          resultItems[activeResultIndex].classList.remove('active-search-result');
        }
        activeResultIndex = (activeResultIndex + 1) % resultItems.length;
        resultItems[activeResultIndex].classList.add('active-search-result');
        resultItems[activeResultIndex].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        if (activeResultIndex >= 0 && activeResultIndex < resultItems.length) {
          resultItems[activeResultIndex].classList.remove('active-search-result');
        }
        activeResultIndex = (activeResultIndex - 1 + resultItems.length) % resultItems.length;
        resultItems[activeResultIndex].classList.add('active-search-result');
        resultItems[activeResultIndex].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      } else if (event.key === 'Enter') {
        if (activeResultIndex >= 0 && activeResultIndex < resultItems.length) {
          event.preventDefault();
          const linkElement = resultItems[activeResultIndex].querySelector('a');
          if (linkElement && linkElement.href) {
            window.location.href = linkElement.href;
          }
        }
      } else if (event.key === 'Escape') {
        resultsContainer.style.display = 'none';
        activeResultIndex = -1;
        if (searchClearBtn) searchClearBtn.style.display = 'none';
      }
    });

    let hideTimeout;
    searchInput.addEventListener('blur', () => {
      hideTimeout = setTimeout(() => {
        resultsContainer.style.display = 'none';
      }, 150);
    });

    resultsContainer.addEventListener('mouseenter', () => {
      clearTimeout(hideTimeout);
    });
    resultsContainer.addEventListener('mouseleave', () => {
      if (document.activeElement !== searchInput) {
          resultsContainer.style.display = 'none';
      }
    });

    searchInput.addEventListener('focus', () => {
      clearTimeout(hideTimeout);
      if (searchInput.value.trim().length >= 2 && resultsContainer.firstChild && resultsContainer.firstChild.innerHTML !== '' && resultsContainer.firstChild.innerHTML !== '<p>No results found.</p>') {
        resultsContainer.style.display = 'block';
        const resultItems = resultsContainer.querySelectorAll('ul li');
        if (activeResultIndex >=0 && activeResultIndex < resultItems.length) {
            // resultItems[activeResultIndex].classList.add('active-search-result');
            // resultItems[activeResultIndex].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
      }
    });

  } else {
    console.warn('Search input field or results container not found in the DOM.');
  }
});
