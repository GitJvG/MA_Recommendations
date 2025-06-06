function feedback() {
    const listenButtons = document.querySelectorAll('.listen-button');

    listenButtons.forEach(button => {
        button.addEventListener('click', function() {
            const albumId = this.closest('tr').dataset.album_id;
            const newStatus = this.dataset.status;
            const bandid = this.closest('tr').dataset.band_id;

            if (!albumId) {
                console.error("Album ID not found for this button.");
                return;
            }

            const buttonContainer = this.closest('.listen-status-controls');
            if (buttonContainer) {
                buttonContainer.querySelectorAll('.listen-button').forEach(otherButton => {
                    otherButton.classList.remove('selected');
                });
                this.classList.add('selected');
            }

            fetch('/update_album_status', { 
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    album_id: albumId,
                    status: newStatus,
                    band_id: bandid
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Album status updated successfully:', data);
            })
            .catch(error => {
                console.error('Error updating album status:', error);
                alert('Failed to update status. Please try again.');
                if (buttonContainer) {
                }
            });
        });
    });
};

feedback();