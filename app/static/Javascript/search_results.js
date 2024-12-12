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

    const headerLi = document.createElement('li');
    headerLi.classList.add('list-group-item', 'results-header');  // Add a class for styling the header row
    headerLi.innerHTML = `
        <div class="results-container">
            <div id="search-result">Band Name</div>
            <div class="search-result">Genre</div>
            <div class="search-result">Country</div>
        </div>
    `;
    
    // Insert the header row as the first item in the list
    RESULTCONTAINER.appendChild(headerLi);
    
    // Loop through the data and create each result item
    data.results.forEach((result) => {
        var li = document.createElement('li');
        li.classList.add('list-group-item');
        li.innerHTML = `
            <div class="results-container">
                <a class="nav-link ajax-link" id="search-result" href="/band/${result.band_id}">${result.name}</a>
                <div class="search-result">${result.genre}</div>
                <div class="search-result">${result.country}</div>
            </div>
        `;
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