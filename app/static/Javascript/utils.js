import { checkAndUpdateBands } from './rightside.js'

export function fetchContent(url, isPopState = false) {
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
        updatePageContent(url, response, isPopState);
    })
    .catch(error => {
        console.error('Failed to load page: ', error);
        alert('An error occurred while loading the page.');
    });
}

function updatePageContent(url, response, isPopState) {
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

    if (response.sidebar) {
        document.getElementById('sidebar').innerHTML = response.sidebar;
    }

    if (!isPopState && window.location.href !== url) {
        history.pushState({ path: url }, '', url);
        console.log('pushed', url)
        checkAndUpdateBands(url);
    };
}

function executeScripts(jsFiles) {
    const existingScripts = document.querySelectorAll('script[data-dynamic-script]');
    existingScripts.forEach(script => script.remove());

    jsFiles.forEach(scriptSrc => {
        const script = document.createElement('script');
        script.src = scriptSrc;
        script.type = 'text/javascript';
        script.async = true;
        script.setAttribute('data-dynamic-script', 'true');
        document.body.appendChild(script);
    });
}

window.addEventListener('DOMContentLoaded', checkAndUpdateBands());