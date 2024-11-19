document.addEventListener('click', function (e) {
    if (e.target.classList.contains('ajax-link')) {
        e.preventDefault();
        var url = e.target.getAttribute('href');

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
            return response.text();
        })
        .then(response => {
            // Replace sidebar and main-content based on URL content
            if (url.includes("logout")) {
                document.getElementById('sidebar').innerHTML = extractHtml(response, '#sidebar');
                document.getElementById('main-content').innerHTML = extractHtml(response, '#main-content');
            } else {
                const mainContent = document.getElementById('main-content');
                // Make sure to check if the content was successfully extracted before assigning it
                const newContent = response
                if (newContent) {
                    mainContent.innerHTML = newContent;
                } else {
                    console.error('Main content not found in the response.');
                }

                var newTitle = extractTitle(response);
                if (newTitle) {
                    document.title = newTitle;
                }
                
                executeScripts(response);
            }
            
            // Push the new URL into the history state
            history.pushState({ path: url }, '', url);
        })
        .catch(error => {
            console.error('Failed to load page: ', error);
            alert('An error occurred while loading the page.');
        });
    }
});

function extractHtml(response, selector) {
    const doc = new DOMParser().parseFromString(response, 'text/html');
    const element = doc.querySelector(selector);
    
    // Return the innerHTML of the element, or null if it doesn't exist
    if (element) {
        return element.innerHTML;
    } else {
        return null;
    }
}

function extractTitle(response) {
    const doc = new DOMParser().parseFromString(response, 'text/html');
    const titleElement = doc.querySelector('title');
    return titleElement ? titleElement.textContent : null;
}

function executeScripts(response) {
    const doc = new DOMParser().parseFromString(response, 'text/html');
    const scripts = doc.querySelectorAll('script');
    scripts.forEach(script => {
        const newScript = document.createElement('script');
        if (script.src) {
            newScript.src = script;
        } else {
            newScript.innerHTML = script.innerHTML;
        }
        document.body.appendChild(newScript);
    });
}
