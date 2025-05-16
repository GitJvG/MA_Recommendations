function ajax_logo() {
    const container = document.getElementById('Band-Container');
    const bandId = container.getAttribute('data-band-id');
    const logoImg = document.getElementById('band-logo');

    if (bandId && logoImg) {
        const url = `/ajax/band_logo/${bandId}`;

        fetch(url)
            .then(response => {
                if (response.ok && response.headers.get('Content-Type').startsWith('image/')) {
                    return response.blob();
                } else {
                    return response.json();
                }
            })
            .then(data => {
                if (data instanceof Blob) {
                    const imageUrl = URL.createObjectURL(data);
                    logoImg.src = imageUrl;
                    logoImg.alt = `Logo for band ID ${bandId}`;
                } else {
                    logoImg.alt = '';
                }
            })
            .catch(error => {
                console.error('Error fetching band logo:', error);
                logoImg.alt = '';
            });
    }
};

ajax_logo();