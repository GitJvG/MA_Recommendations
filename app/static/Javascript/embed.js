function fetchVideo(bandName, albumName, AlbumType) {
  AlbumType = (AlbumType === 'Full-length') ? 'Full Album' : AlbumType;
  const searchQuery = `${bandName} ${albumName} ${AlbumType}`;
  const url = `/ajax/youtube_search?q=${encodeURIComponent(searchQuery)}`;

  fetch(url)
    .then(response => response.json())
    .then(data => {
      if (data && data.video_url) {
        const videoEmbedUrl = data.video_url;
        createFloatingWindow(videoEmbedUrl)
      } else {
        alert('No video found for this album and band.');
      }
    })
    .catch(error => {
      console.error('Error fetching YouTube video:', error);
    });
}