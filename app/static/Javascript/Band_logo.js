function ajax_logo() {
    const container = document.getElementById('Band-Container');
    const bandId = container.getAttribute('data-band-id');
    const logoImg = document.getElementById('band-logo');

    if (bandId && logoImg) {
        const url = `/ajax/band_logo/${bandId}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data) {
                    logoImg.src = data;
                    logoImg.alt = `Logo for band ID ${bandId}`;
                } else {
                    logoImg.alt = 'Logo not available';
                }
            })
            .catch(error => {
                console.error('Error fetching band logo:', error);
                logoImg.alt = 'Error loading logo';
            });
    }
    else console.log('Fail')
};

ajax_logo()