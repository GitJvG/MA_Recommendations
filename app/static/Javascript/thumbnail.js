function displayRecommendedAlbums(albums) {
    const albumContainer = document.querySelector('.album-cards');
    albumContainer.innerHTML = "";

    albums.forEach(album => {
        const albumCard = document.createElement("div");
        albumCard.className = "album-card";

        let videoEmbedUrl;
        if (album.playlist_url) {
            videoEmbedUrl = album.playlist_url;}
        else {
            videoEmbedUrl = album.video_url;}
    
        const albumLink = document.createElement("a");
        albumLink.href = videoEmbedUrl;



    
        const albumImage = document.createElement("img");
        if (album.video_url) {
            albumImage.src = `https://img.youtube.com/vi/${getYouTubeVideoId(album.video_url)}/0.jpg`;
            albumImage.alt = `Thumbnail for ${album.album_name}`;
        } else {
            albumImage.src = "path/to/placeholder_image.jpg";
        }
        albumImage.classList.add("album-thumbnail");
    
        albumImage.addEventListener('click', function (event) {
            event.preventDefault();
            if (videoEmbedUrl) {
                createFloatingWindow(videoEmbedUrl);
            }
        });
    
        const overlay = document.createElement("div");
        overlay.className = "overlay";
    
        const bandLink = document.createElement("a");
        bandLink.href = `/band/${album.band_id}`;
        bandLink.className = "overlay ajax-link";
    
        const bandName = document.createElement("p");
        bandName.textContent = `${album.name} - ${album.album_name}`;
        bandName.className = "band-name";
    
        const genre = document.createElement("p");
        genre.textContent = `${album.genre}`;
        genre.className = "genre";
    
        bandLink.appendChild(bandName);
        bandLink.appendChild(genre);
    
        overlay.appendChild(bandLink);
    
        albumLink.appendChild(albumImage);
        albumLink.appendChild(overlay);
    
        albumCard.appendChild(albumLink);
        albumContainer.appendChild(albumCard);
    });
}

function getYouTubeVideoId(url) {
    const match = url.match(/youtube\.com\/embed\/([a-zA-Z0-9_-]+)/);
    return match ? match[1] : null;
}

fetch('/ajax/recommended_albums')
    .then(response => response.json())
    .then(albums => {
        displayRecommendedAlbums(albums);
    })
    .catch(err => console.error("Error loading albums:", err));
