function fetchVideo(bandName, albumName, AlbumType) {
  const searchQuery = `${bandName} ${albumName} ${AlbumType}`;
  const url = `/ajax/youtube_search?q=${encodeURIComponent(searchQuery)}`;

  fetch(url)
    .then(response => response.json())
    .then(data => {
      if (data && data.video_url) {
        const videoEmbedUrl = data.video_url;

        const iframe = document.createElement('iframe');
        iframe.src = videoEmbedUrl;
        iframe.width = '560';
        iframe.height = '315';
        iframe.allow = 'accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture';
        iframe.allowFullscreen = true;
        iframe.classList.add('floating-video');

        const closeBtn = document.createElement('button');
        closeBtn.classList.add('close-btn');
        closeBtn.innerHTML = '&times;';

        closeBtn.addEventListener('click', function () {
          iframe.remove();
          closeBtn.remove();
        });

        document.body.appendChild(iframe);
        iframe.appendChild(closeBtn);
      } else {
        alert('No video found for this album and band.');
      }
    })
    .catch(error => {
      console.error('Error fetching YouTube video:', error);
    });
}

