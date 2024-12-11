function loadBandData(route, containerSelector, rowsCount = 1) {
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
                container.innerHTML = "<p>No bands available or not logged in.</p>";
                return;
            }

            const itemsPerRow = Math.ceil(data.length / rowsCount);

            // Flatten all rows inside the same container
            for (let i = 1; i <= rowsCount; i++) {
                const rowData = data.slice((i - 1) * itemsPerRow, i * itemsPerRow);

                rowData.forEach(band => {
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

                    container.appendChild(bandCard); // Append all cards to the same container
                });
            }

            // Set the number of rows in a CSS variable
            container.style.setProperty('--rows-count', rowsCount);
        })
        .catch(error => {
            console.error(`Error loading data from ${route}:`, error);
        });
}

function refresh() {
    loadBandData('/ajax/featured', '.band-cards');
    loadBandData('/ajax/recommended', '.recommendation-cards', 2);
    loadBandData('/ajax/remind', '.reminder-cards');
}

refresh();
