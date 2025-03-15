if (!window.likeButtonListenerAdded) {
    window.likeButtonListenerAdded = true;
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
                    const likeBtn = document.querySelector(`.like-btn[data-band-id="${bandId}"][data-action="like"]`);
                    const dislikeBtn = document.querySelector(`.like-btn[data-band-id="${bandId}"][data-action="dislike"]`);
    
                    if (action === 'like') {
                        likeBtn.classList.add('active');
                        likeBtn.classList.remove('inactive');
                        dislikeBtn.classList.remove('active');
                        dislikeBtn.classList.add('inactive');
                    } else if (action === 'dislike') {
                        dislikeBtn.classList.add('active');
                        dislikeBtn.classList.remove('inactive');
                        likeBtn.classList.remove('active');
                        likeBtn.classList.add('inactive');
                    }
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
}