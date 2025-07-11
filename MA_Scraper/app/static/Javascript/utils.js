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
        const pageTitle = response.title || 'Amplifier Worship';
        document.title = pageTitle;
    }

    if (response.sidebar) {
        document.getElementById('sidebar').innerHTML = response.sidebar;
    }

    if (response.js_files && Array.isArray(response.js_files)) {
        executeScripts(response.js_files);
    }

    const mainContent = document.getElementById('main-content');

    mainContent.classList.remove("index");
    if (response.main_content_class.trim() !== "") {
        mainContent.classList.add(response.main_content_class);
    }

    if (!isPopState && window.location.href !== url) {
        history.pushState({ path: url }, '', url);
    };
}

function executeScripts(js_files) {
    const existingScripts = document.querySelectorAll('script[data-dynamic-script]');
    existingScripts.forEach(script => script.remove());

    js_files.forEach(scriptSrc => {
        const script = document.createElement('script');
        script.src = scriptSrc;
        script.type = 'text/javascript';
        script.async = true;
        script.setAttribute('data-dynamic-script', 'true');
        document.body.appendChild(script);
    });
}

window.create_like_dislike = function create_like_dislike(band) {
    return `
        <div>
            <a class="nav-link ajax-link" href="/band/${band.band_id}">${band.name}</a>
            <p>Status: ${band.liked === true ? 'Liked' : 'Not Liked'}</p>
        </div>
        <div>
            <button class="btn btn-success btn-sm like-btn ${band.liked ? 'active' : ''}" 
                    data-band-id="${band.band_id}" 
                    data-action="like">
                Like
            </button>
            <button class="btn btn-danger btn-sm like-btn ${!band.liked ? 'disabled' : ''}" 
                    data-band-id="${band.band_id}" 
                    data-action="dislike">
                Dislike
            </button>
        </div>
    `;
}

window.createFloatingWindow = function createFloatingWindow(videoEmbedUrl, bandName, bandId, albumName) {
    const videoWrapper = document.createElement('div');
    videoWrapper.classList.add('floating-video-wrapper');
    
    const iframewrap = document.createElement('div');
    iframewrap.classList.add('iframewrap');

    const iframe = document.createElement('iframe');
    iframe.src = videoEmbedUrl;
    iframe.allow = 'accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture';
    iframe.allowFullscreen = true;

    iframewrap.appendChild(iframe)

    const header = document.createElement('div');
    header.classList.add('floating-video-header');

    const titleContainer = document.createElement('div');
    titleContainer.classList.add('floating-video-title-container');

    const bandLink = document.createElement('a');
    bandLink.classList.add('nav-link', 'ajax-link');
    bandLink.href = `/band/${bandId}`;
    bandLink.textContent = bandName;
    const separator = document.createTextNode(' - ');
    const albumText = document.createElement('span');
    albumText.textContent = albumName;

    titleContainer.appendChild(bandLink);
    titleContainer.appendChild(separator);
    titleContainer.appendChild(albumText);

    const closeBtn = document.createElement('button');
    closeBtn.classList.add('close-btn');

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.classList.add('close-btn-svg');

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z');

    svg.appendChild(path);
    closeBtn.appendChild(svg);

    header.appendChild(titleContainer);
    header.appendChild(closeBtn);

    closeBtn.addEventListener('click', function () {
      videoWrapper.remove();
    });
    
    videoWrapper.appendChild(header);
    videoWrapper.appendChild(iframewrap);
    
    document.body.appendChild(videoWrapper);
    makeResizable(videoWrapper);
  }
  
function makeResizable(wrapper) {
    const resizer = document.createElement('div');
    resizer.classList.add('resizer');

    const resizerSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    resizerSvg.setAttribute('viewBox', '0 0 24 24');
    resizerSvg.classList.add('resizer-icon-svg');

    const resizerPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    resizerPath.setAttribute('d', 'M6 6L18 18m0 -12h-12v12');

    resizerSvg.appendChild(resizerPath);
    resizer.appendChild(resizerSvg);

    wrapper.querySelector('.floating-video-header').prepend(resizer);

    let isResizing = false;

    resizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        document.body.style.cursor = 'se-resize';

        initialWidth = wrapper.offsetWidth;
        initialHeight = wrapper.offsetHeight;
        initialMouseX = e.clientX;
        initialMouseY = e.clientY;
    });

    let initialWidth, initialHeight, initialMouseX, initialMouseY;

    document.addEventListener('mousemove', (e) => {
        if (isResizing) {
            const deltaX = initialMouseX - e.clientX;
            const deltaY = initialMouseY - e.clientY;

            wrapper.style.width = `${initialWidth + deltaX}px`;
            wrapper.style.height = `${initialHeight + deltaY}px`;
        }
    });

    document.addEventListener('mouseup', () => {
        isResizing = false;
        document.body.style.cursor = 'auto';
    });
}