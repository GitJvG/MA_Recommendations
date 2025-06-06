function fetchVideo(bandName, id, albumName, AlbumType) {
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

        createFloatingWindow(videoEmbedUrl, bandName, id, albumName)
      } else {
        alert('No video found for this album and band.');
      }
    })
    .catch(error => {
      console.error('Error fetching YouTube video:', error);
    });
}

document.querySelectorAll('.clickable-album-name').forEach(span => {
    span.addEventListener('click', event => {
      const band_id = span.closest('tr').dataset.band_id
      const name = span.dataset.name;
      const album = span.dataset.album;
      const type = span.closest('tr').dataset.type;
      fetchVideo(name, band_id, album, type);
    });
});