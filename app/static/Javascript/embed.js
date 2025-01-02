function fetchVideo(bandName, albumName, AlbumType) {
  AlbumType = (AlbumType === 'Full-length') ? 'Full Album' : AlbumType;
  const searchQuery = `${bandName} ${albumName} ${AlbumType}`;
  const url = `/ajax/youtube_search?q=${encodeURIComponent(searchQuery)}`;

  fetch(url)
    .then(response => response.json())
    .then(data => {
      if (data && data.video_url) {
        let videoEmbedUrl;

        if (data.playlist_url) {
            videoEmbedUrl = data.playlist_url;}
        else {
            videoEmbedUrl = data.video_url;}

        createFloatingWindow(videoEmbedUrl, data.video_url)
      } else {
        alert('No video found for this album and band.');
      }
    })
    .catch(error => {
      console.error('Error fetching YouTube video:', error);
    });
}

document.querySelectorAll('.watch-video').forEach(button => {
  button.addEventListener('click', event => {
      const name = button.dataset.name;
      const album = button.dataset.album;
      const type = button.dataset.type;

      fetchVideo(name, album, type);
  });
});