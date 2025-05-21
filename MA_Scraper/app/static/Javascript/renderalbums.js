export function loadData(route, containerSelector, type, bands=null, count=null) {
    const url = new URL(route, window.location.origin);
    const params = new URLSearchParams();
    if (bands) {
        params.append("bands", bands);
    }
    if (count) {
        params.append("count", count);
    }
    if (params.toString()) {
        url.search = params.toString();
    }
    
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to fetch data from ${route}`);
            }
            return response.json();
        })
        .then(data => {
            const container = document.querySelector(containerSelector);
            container.innerHTML = "";

            if (data.length === 0) {
                container.innerHTML = "<p>No items available or not logged in.</p>";
                return;
            }
            const rowsCount = data.rowsCount;
            const items = data.data

            for (let i = 1; i <= rowsCount; i++) {
                const rowData = items.slice((i - 1) * count, i * count);

                rowData.forEach(item => {
                    let card;

                    if (type === "album") {
                        card = createAlbumCard(item);
                    } 
                    if (card) {
                        container.appendChild(card);
                    }
                });
            }

            container.style.setProperty('--rows-count', rowsCount);
            container.style.setProperty('--albums-per-row', count);
        })
        .catch(error => {
            console.error(`Error loading data from ${route}:`, error);
        });
}

function createAlbumCard(album) {
    const albumContainer = document.createElement("div");
    const albumCard = document.createElement("div");

    albumContainer.className = "album-container"
    albumCard.className = "album-card";

    let videoEmbedUrl = album.playlist_url || album.video_url;
    let thumbnail_url = album.thumbnail_url

    const albumLink = document.createElement("a");
    albumLink.href = videoEmbedUrl;

    const albumImage = document.createElement("img");
    albumImage.src = videoEmbedUrl
        ? thumbnail_url
        : "path/to/placeholder_image.jpg";
    albumImage.alt = ``;
    albumImage.classList.add("album-thumbnail");

    albumImage.addEventListener("click", function (event) {
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

    const overlaytext = document.createElement("div");
    overlaytext.className = "overlay-text";

    const bandName = document.createElement("p");
    bandName.textContent = `${album.name}`;
    bandName.className = "band-name";

    const AlbumName = document.createElement("p");
    AlbumName.textContent = `${album.album_name}`;
    AlbumName.className = "album";

    const genre = document.createElement("p");
    genre.textContent = `${album.genre}`;
    genre.className = "genre";

    overlaytext.appendChild(AlbumName);
    overlaytext.appendChild(bandName);
    bandLink.appendChild(overlaytext);
    overlay.appendChild(bandLink);
    albumLink.appendChild(albumImage);

    albumCard.appendChild(albumLink);
    albumContainer.appendChild(albumCard)
    albumContainer.appendChild(overlay);

    return albumContainer;
}