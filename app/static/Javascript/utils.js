export function fetchContent(url) {
    fetch(url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(response => {
        updatePageContent(url, response);
    })
    .catch(error => {
        console.error('Failed to load page: ', error);
        alert('An error occurred while loading the page.');
    });
}

function updatePageContent(url, response) {
    // Replace sidebar and main-content based on URL content
    if (response.html) {
        const mainContent = document.getElementById('main-content');
        mainContent.innerHTML = response.html;
    }

    if (response.title) {
        const pageTitle = response.title || 'Metallum Recommender';
        document.title = pageTitle;
    }

    if (response.js_files && Array.isArray(response.js_files)) {
        executeScripts(response.js_files);
    }

    // Push the new URL into the history state
    history.pushState({ path: url }, '', url);
}

function executeScripts(jsFiles) {
    // Remove previously appended script tags with matching sources
    const existingScripts = document.querySelectorAll('script[data-dynamic-script]');
    existingScripts.forEach(script => script.remove());

    // Append new script tags
    jsFiles.forEach(scriptSrc => {
        const script = document.createElement('script');
        script.src = scriptSrc;
        script.type = 'text/javascript';
        script.async = true; // Optional: Load scripts asynchronously
        script.setAttribute('data-dynamic-script', 'true'); // Tag it for easy identification
        document.body.appendChild(script);
    });
}

