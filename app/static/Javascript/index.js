fetch('/ajax/featured')
    .then(response => {
        if (!response.ok) {
            throw new Error("Failed to fetch featured bands");
        }
        return response.json();
    })
    .then(data => {
        const container = document.querySelector(".band-cards");
        container.innerHTML = ""; // Clear any existing content

        if (data.length === 0) {
            container.innerHTML = "<p>No featured bands available.</p>";
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
        console.error("Error loading featured bands:", error);
    });