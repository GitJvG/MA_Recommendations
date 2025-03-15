function loadData(route, containerSelector, type, rowsCount = 1) {
    fetch(route)
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

            const itemsPerRow = Math.ceil(data.length / rowsCount);

            for (let i = 1; i <= rowsCount; i++) {
                const rowData = data.slice((i - 1) * itemsPerRow, i * itemsPerRow);

                rowData.forEach(item => {
                    let card;

                    if (type === "album") {
                        card = createAlbumCard(item);
                    } else if (type === "band") {
                        card = createBandCard(item);
                    }

                    if (card) {
                        container.appendChild(card);
                    }
                });
            }

            addScrolling(container);
            container.style.setProperty('--rows-count', rowsCount);
        })
        .catch(error => {
            console.error(`Error loading data from ${route}:`, error);
        });
}

function createAlbumCard(album) {
    const albumCard = document.createElement("div");
    albumCard.className = "album-card";

    let videoEmbedUrl = album.playlist_url || album.video_url;

    const albumLink = document.createElement("a");
    albumLink.href = videoEmbedUrl;

    const albumImage = document.createElement("img");
    albumImage.src = album.video_url
        ? `https://img.youtube.com/vi/${getYouTubeVideoId(album.video_url)}/0.jpg`
        : "path/to/placeholder_image.jpg";
    albumImage.alt = `Thumbnail for ${album.album_name}`;
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

    return albumCard;
}

function createBandCard(band) {
    const bandCard = document.createElement("a");
    bandCard.href = `/band/${band.band_id}`;
    bandCard.className = "band-card ajax-link";
    
    if (band.liked) {
        bandCard.classList.add("liked");
    }

    bandCard.innerHTML = `
        <h3>${band.name}</h3>
        <p class="genre">${band.genre}</p>
    `;

    return bandCard;
}

// Function to add scrolling behavior
function addScrolling(container) {
    const initialScrollSpeed = 3;
    const maxScrollSpeed = 100;
    const acceleration = 0.2;
    const extra_acc = 0.005
    const scrollIntervalTime = 1;
    let scrollInterval;
    let currentSpeed = initialScrollSpeed;

    function startScrolling(direction) {
        stopScrolling();
        currentSpeed = initialScrollSpeed;
        scrollInterval = setInterval(() => {
            container.scrollLeft += direction * currentSpeed;

            if (currentSpeed < maxScrollSpeed) {
                currentSpeed += acceleration;
                currentSpeed = currentSpeed * (1+extra_acc);
            }
        }, scrollIntervalTime);
    }

    function stopScrolling() {
        clearInterval(scrollInterval);
    }

    const rightArrowButton = document.createElement("div");
    rightArrowButton.className = "right-arrow-button";
    rightArrowButton.innerHTML = '→';
    rightArrowButton.addEventListener("click", () => {
        container.scrollBy({
            left: 400,
            behavior: "smooth",
        });
    });

    rightArrowButton.addEventListener("mouseenter", () => startScrolling(1));
    rightArrowButton.addEventListener("mouseleave", stopScrolling);

    const leftArrowButton = document.createElement("div");
    leftArrowButton.className = "left-arrow-button";
    leftArrowButton.innerHTML = '←';
    leftArrowButton.addEventListener("click", () => {
        container.scrollBy({
            left: -400,
            behavior: "smooth",
        });
    });

    leftArrowButton.addEventListener("mouseenter", () => startScrolling(-1));
    leftArrowButton.addEventListener("mouseleave", stopScrolling);

    container.appendChild(leftArrowButton);
    container.appendChild(rightArrowButton);

    function updateArrowVisibility() {
        const scrollLeft = container.scrollLeft;
        const maxScrollLeft = container.scrollWidth - container.clientWidth;

        if (scrollLeft < maxScrollLeft && isHovered) {
            rightArrowButton.style.display = "block";
        } else {
            rightArrowButton.style.display = "none";
        }

        if (scrollLeft > 0 && isHovered) {
            leftArrowButton.style.display = "block";
        } else {
            leftArrowButton.style.display = "none";
        }
    }

    let isHovered = false;

    rightArrowButton.style.display = "none";
    leftArrowButton.style.display = "none";

    container.addEventListener("mouseenter", () => {
        isHovered = true;
        updateArrowVisibility();
    });

    container.addEventListener("mouseleave", () => {
        isHovered = false;
        updateArrowVisibility();
    });

    container.addEventListener("scroll", updateArrowVisibility);
    updateArrowVisibility();
}

function getYouTubeVideoId(url) {
    const match = url.match(/youtube\.com\/embed\/([a-zA-Z0-9_-]+)/);
    return match ? match[1] : null;
}

function refresh() {
    loadData("/ajax/featured", ".band-cards", "album");
    loadData("/ajax/recommended_albums", ".album-cards", "album", 3);
    loadData("/ajax/remind", ".reminder-cards", "album");
    loadData("/ajax/known_albums", ".known_album-cards", "album", 3)
}

refresh();