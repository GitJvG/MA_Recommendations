document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('click', function(event) {
        if (event.target && event.target.matches('.like-btn')) {
            const bandId = event.target.getAttribute('data-band-id');
            const action = event.target.getAttribute('data-action');

            fetch('/like_band', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    band_id: bandId,
                    action: action
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to like/dislike band.');
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    document.querySelectorAll(`.like-btn[data-band-id="${bandId}"]`).forEach(btn => {
                        if (btn.getAttribute('data-action') === action) {
                            btn.classList.add('disabled');
                        } else {
                            btn.classList.remove('disabled');
                        }
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }

        if (event.target && event.target.matches('.remind-btn')) {
            const bandId = event.target.getAttribute('data-band-id');
            const action = 'remind_me';

            fetch('/like_band', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    band_id: bandId,
                    action: action
                })
            })
            .then(response => response.json())
            .then(data => {
                const currentState = event.target.classList.contains('active') ? 'active' : 'inactive';
                const newState = currentState === 'active' ? 'inactive' : 'active';

                event.target.classList.remove(currentState);
                event.target.classList.add(newState);
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }
    });
});
