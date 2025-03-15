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

    if (response.js_files && Array.isArray(response.js_files)) {
        executeScripts(response.js_files);
    }

    if (response.sidebar) {
        document.getElementById('sidebar').innerHTML = response.sidebar;
    }

    const mainContent = document.getElementById('main-content');

    mainContent.classList.remove("index");
    if (response.main_content_class.trim() !== "") {
        mainContent.classList.add(response.main_content_class);
    }

    if (!isPopState && window.location.href !== url) {
        history.pushState({ path: url }, '', url);
        console.log('pushed', url)
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

window.createFloatingWindow = function createFloatingWindow(videoEmbedUrl) {
    const videoWrapper = document.createElement('div');
    videoWrapper.classList.add('floating-video-wrapper');
  
    const iframe = document.createElement('iframe');
    iframe.src = videoEmbedUrl;
    iframe.width = '560';
    iframe.height = '315';
    iframe.allow = 'accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture';
    iframe.allowFullscreen = true;
  
    const closeBtn = document.createElement('button');
    closeBtn.classList.add('close-btn');
    closeBtn.innerHTML = '&times;';
  
    closeBtn.addEventListener('click', function () {
      videoWrapper.remove();
    });
  
    videoWrapper.appendChild(iframe);
    videoWrapper.appendChild(closeBtn);
  
    document.body.appendChild(videoWrapper);
    makeResizable(videoWrapper);
  }
  
function makeResizable(wrapper) {
    const resizer = document.createElement('div');
    resizer.classList.add('resizer');
    wrapper.appendChild(resizer);
  
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