function fetchVideo(bandName, albumName, AlbumType) {
  AlbumType = (AlbumType === 'Full-length') ? 'Full Album' : AlbumType;
  const searchQuery = `${bandName} ${albumName} ${AlbumType}`;
  const url = `/ajax/youtube_search?q=${encodeURIComponent(searchQuery)}`;

  fetch(url)
    .then(response => response.json())
    .then(data => {
      if (data && data.video_url) {
        const videoEmbedUrl = data.video_url;

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
      } else {
        alert('No video found for this album and band.');
      }
    })
    .catch(error => {
      console.error('Error fetching YouTube video:', error);
    });
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