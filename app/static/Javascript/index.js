function loadBandData(route, containerSelector) {
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
                container.innerHTML = "<p>No bands available.</p>";
            } else {
                data.forEach(band => {
                    const bandCard = document.createElement("a");
                    bandCard.href = `/band/${band.band_id}`;
                    bandCard.className = "band-card ajax-link";

                    bandCard.innerHTML = `
                        <h3>${band.name}</h3>
                    `;

                    container.appendChild(bandCard);
                });
            }
        })
        .catch(error => {
            console.error(`Error loading data from ${route}:`, error);
        });
}

function refresh() {
    loadBandData('/ajax/featured', '.band-cards');
    loadBandData('/ajax/recommended', '.recommendation-cards');
};

refresh()