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
        const pageTitle = response.title || 'Amplifier Worship';
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
    };
    checkAndUpdateBands();
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
            <button class="btn btn-success btn-sm like-btn ${band.liked ? 'disabled' : ''}" 
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

window.createFloatingWindow = function createFloatingWindow(videoEmbedUrl, video_url) {
    // videoEmbedUrl can be either a video or playlist url, video_url is always a video (used for adding to playlist, but less complete than videoEmbedUrl)
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

    const addToPlaylistBtn = document.createElement('button');
    addToPlaylistBtn.classList.add('add-to-playlist-btn');
    addToPlaylistBtn.textContent = 'Add to Playlist';

    addToPlaylistBtn.addEventListener('click', function () {
        openPlaylistModal(videoEmbedUrl);
    });
  
    videoWrapper.appendChild(iframe);
    videoWrapper.appendChild(closeBtn);
    videoWrapper.appendChild(addToPlaylistBtn)
  
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

function openPlaylistModal(video_url) {
    let modal = document.getElementById('playlist-modal');
    if (!modal) {
      // Create modal element
      modal = document.createElement('div');
      modal.id = 'playlist-modal';
      modal.style.position = 'fixed';
      modal.style.top = '50%';
      modal.style.left = '50%';
      modal.style.transform = 'translate(-50%, -50%)';
      modal.style.background = '#fff';
      modal.style.border = '1px solid #ccc';
      modal.style.padding = '20px';
      modal.style.zIndex = '1000';
      modal.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.5)';
      modal.style.display = 'none'; // Hidden by default
  
      // Modal title
      const modalTitle = document.createElement('h3');
      modalTitle.textContent = 'Select a Playlist';
  
      // Playlist list container
      const playlistList = document.createElement('ul');
      playlistList.id = 'playlist-list';
  
      // Close button
      const closeModalBtn = document.createElement('button');
      closeModalBtn.textContent = 'Close';
      closeModalBtn.style.marginTop = '10px';
      closeModalBtn.addEventListener('click', () => {
        modal.style.display = 'none';
      });
  
      // Append elements to modal
      modal.appendChild(modalTitle);
      modal.appendChild(playlistList);
      modal.appendChild(closeModalBtn);
  
      // Append modal to document body
      document.body.appendChild(modal);
    }
  
    // Make modal visible
    modal.style.display = 'block';

    fetch('/api/get_user_playlists')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const playlistList = document.getElementById('playlist-list');
                playlistList.innerHTML = '';

                data.playlists.forEach(playlist => {
                    const li = document.createElement('li');
                    li.textContent = playlist.title;
                    li.dataset.playlistId = playlist.id;

                    li.addEventListener('click', () => addVideoToPlaylist(playlist.id, video_url));
                    playlistList.appendChild(li);
                });
            } else {
                alert(`Failed to fetch playlists: ${data.error}`);
            }
        })
        .catch(err => console.error('Error fetching playlists:', err));
}

function addVideoToPlaylist(playlistId, videoId) {
    fetch('/api/add_video_to_playlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ videoId, playlistId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Video added successfully!');
        } else {
            alert(`Failed to add video: ${data.error}`);
        }

        const modal = document.getElementById('playlist-modal');
        modal.style.display = 'none';
    })
    .catch(err => console.error('Error adding video:', err));
}