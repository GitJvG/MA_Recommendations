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
            const rightArrowButton = document.createElement("div");
            rightArrowButton.className = "right-arrow-button";
            rightArrowButton.innerHTML = '→';
            rightArrowButton.addEventListener('click', () => {
                container.scrollBy({
                    left: 200,
                    behavior: 'smooth'
                });
            });

            // Create the left arrow button
            const leftArrowButton = document.createElement("div");
            leftArrowButton.className = "left-arrow-button";
            leftArrowButton.innerHTML = '←';
            leftArrowButton.addEventListener('click', () => {
                container.scrollBy({
                    left: -200,
                    behavior: 'smooth'
                });
            });

            container.appendChild(leftArrowButton);
            container.appendChild(rightArrowButton);

            function updateArrowVisibility() {
                const scrollLeft = container.scrollLeft;
                const maxScrollLeft = container.scrollWidth - container.clientWidth;
            
                if (scrollLeft < maxScrollLeft && isHovered) {
                    rightArrowButton.style.display = 'block';
                } else {
                    rightArrowButton.style.display = 'none';
                }
            
                if (scrollLeft > 0 && isHovered) {
                    leftArrowButton.style.display = 'block';
                } else {
                    leftArrowButton.style.display = 'none';
                }
            }
            
            let isHovered = false;
            
            rightArrowButton.style.display = 'none';
            leftArrowButton.style.display = 'none';
            
            container.addEventListener('mouseenter', () => {
                isHovered = true;
                updateArrowVisibility();
            });
            
            container.addEventListener('mouseleave', () => {
                isHovered = false;
                updateArrowVisibility();
            });
            
            container.addEventListener('scroll', updateArrowVisibility);
            updateArrowVisibility();
            
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