async function fetchSearchResults(query, page = 1) {
    const response = await fetch(`/search_results?query=${encodeURIComponent(query)}&page=${page}`, {
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
    const PAGINATION = document.getElementById('pagination');

    SEARCHHEADER.textContent = `Search Results for "${query}"`;
    RESULTCONTAINER.innerHTML = '';
    MESSAGE.textContent = '';

    if (!data.results || data.results.length === 0) {
        MESSAGE.textContent = `No results found for "${query}".`;
        PAGINATION.innerHTML = ''; // No pagination if there are no results
        return;
    }

    const headerLi = document.createElement('li');
    headerLi.classList.add('list-group-item', 'results-header');
    headerLi.innerHTML = `
        <div class="results-container">
            <div id="search-result">Band Name</div>
            <div class="search-result">Genre</div>
            <div class="search-result">Country</div>
        </div>
    `;
    RESULTCONTAINER.appendChild(headerLi);

    data.results.forEach((result) => {
        const li = document.createElement('li');
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

    // Render pagination controls
    if (data.total_pages > 1) {
        PAGINATION.innerHTML = ''; // Clear existing pagination controls
        for (let i = 1; i <= data.total_pages; i++) {
            const pageLink = document.createElement('a');
            pageLink.href = "#";
            pageLink.textContent = i;
            pageLink.classList.add('pagination-link');
            if (i === data.current_page) {
                pageLink.classList.add('active'); // Highlight the current page
            }

            // Add event listener to handle page change
            pageLink.addEventListener('click', (e) => {
                e.preventDefault();
                fetchPageResults(query, i);
            });

            PAGINATION.appendChild(pageLink);
        }
    }
}

// Function to fetch and render search results for a specific page
function fetchPageResults(query, page) {
    fetchSearchResults(query, page)
        .then((data) => {
            renderSearchResults(data, query);
        })
        .catch((error) => {
            console.error('An error occurred while fetching search results:', error);
            document.getElementById('no-results-message').textContent = `An error occurred: ${error.message}`;
        });
}

// Function to handle the initial search results fetch
function handleSearchResults() {
    const SEARCHHEADER = document.getElementById('search-header');
    const QUERY = SEARCHHEADER.getAttribute('data-query');

    if (QUERY) {
        fetchPageResults(QUERY, 1);
    } else {
        document.getElementById('no-results-message').textContent = 'No search query provided.';
    }
}

handleSearchResults();
