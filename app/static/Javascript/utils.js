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
    if (url.includes("logout")) {
        document.getElementById('sidebar').innerHTML = extractHtml(response.html, '#sidebar');
        document.getElementById('main-content').innerHTML = extractHtml(response.html, '#main-content');
    } else {
        const mainContent = document.getElementById('main-content');
        // Ensure that the content is not empty
        if (response.html) {
            mainContent.innerHTML = response.html;
        } else {
            console.error('Main content not found in the response.');
        }

        if (response.title) {
            const pageTitle = response.title || 'Metallum Recommender';
            document.title = pageTitle;
        }

        // Execute scripts from response.js_files
        if (response.js_files && Array.isArray(response.js_files)) {
            executeScripts(response.js_files);
        }
    }

    // Push the new URL into the history state
    history.pushState({ path: url }, '', url);
}

function extractHtml(htmlContent, selector) {
    const doc = new DOMParser().parseFromString(htmlContent, 'text/html');
    const element = doc.querySelector(selector);
    return element ? element.innerHTML : null;
}

function executeScripts(jsFiles) {
    jsFiles.forEach(scriptSrc => {
        const script = document.createElement('script');
        script.src = scriptSrc;
        script.type = 'text/javascript';
        script.async = true;  // Optional: Load scripts asynchronously
        document.body.appendChild(script);
    });
}
