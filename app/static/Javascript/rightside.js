function fetchSimilarBands(bandId) {
    fetch(`/ajax/similar_bands/${bandId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch similar bands');
            }
            return response.json();
        })
        .then(data => {
            displaySimilarBands(data);
        })
        .catch(error => {
            console.error('Error loading similar bands:', error);
        });
}

function displaySimilarBands(bands) {
    const rightSideDiv = document.querySelector('.rightside');
    rightSideDiv.innerHTML = ''; // Clear the current content

    if (bands.length === 0) {
        rightSideDiv.innerHTML = "<p>No similar bands found.</p>";
        return;
    }

    // Create a container for the band boxes
    const bandContainer = document.createElement('div');
    bandContainer.className = 'band-container';

    bands.forEach(band => {
        const bandBox = document.createElement('div');
        bandBox.className = 'band-box';
    
        if (band.liked) {
            bandBox.classList.add("liked");
        }

        const bandLink = document.createElement('a');
        bandLink.href = `/band/${band.band_id}`;
        bandLink.className = 'nav-link ajax-link';

        bandLink.innerHTML = `
            <div class="band_name">${band.name}</div>
            <p class="genre">${band.genre}</p>
        `;
    
        bandBox.appendChild(bandLink);
        bandContainer.appendChild(bandBox);
    });
    rightSideDiv.appendChild(bandContainer);
}

function clearSimilarBands() {
    const rightSideDiv = document.querySelector('.rightside');
    if (rightSideDiv) {
        rightSideDiv.innerHTML = '';
    }
}

export function checkAndUpdateBands(url=null) {
    url = url || window.location.pathname;
    if (url.startsWith('/band/')) {
        const container = document.querySelector('[data-band-id]');
        const bandId = container ? container.getAttribute('data-band-id') : null;

        if (bandId) {
            fetchSimilarBands(bandId);
        }
    } else {
        clearSimilarBands();
    }
}

checkAndUpdateBands()