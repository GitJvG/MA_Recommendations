async function fetchSearchResults(query) {
    const response = await fetch(`/search_results?query=${encodeURIComponent(query)}`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}

function renderSearchResults(data, query) {
    const SEARCHHEADER = document.getElementById('search-header');
    const RESULTCONTAINER = document.getElementById('search-results');
    const MESSAGE = document.getElementById('no-results-message');

    SEARCHHEADER.textContent = `Search Results for "${query}"`;
    RESULTCONTAINER.innerHTML = '';
    MESSAGE.textContent = '';

    if (!data.results || data.results.length === 0) {
        MESSAGE.textContent = `No results found for "${query}".`;
        return;
    }

    // Populate the results list
    data.results.forEach((result) => {
        var li = document.createElement('li');
        li.classList.add('list-group-item');
        li.innerHTML = `<a href="/band/${result.band_id}">${result.name}</a>`;
        RESULTCONTAINER.appendChild(li);
    });
}

function handleSearchResults() {
    const SEARCHHEADER = document.getElementById('search-header');
    const QUERY = SEARCHHEADER.getAttribute('data-query');

    if (QUERY) {
        fetchSearchResults(QUERY)
            .then((data) => {
                renderSearchResults(data, QUERY);
            })
            .catch((error) => {
                console.error('An error occurred while fetching search results:', error);
                document.getElementById('no-results-message').textContent = `An error occurred: ${error.message}`;
            });
    } else {
        document.getElementById('no-results-message').textContent = 'No search query provided.';
    }
}

handleSearchResults();