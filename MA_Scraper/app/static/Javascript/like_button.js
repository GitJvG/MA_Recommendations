if (!window.likeButtonListenerAdded) {
    window.likeButtonListenerAdded = true;
    document.addEventListener('click', function(event) {
        let bandId = null;
        let action = null;
        let targetButton = null;

        if (event.target && event.target.matches('.like-btn')) {
            bandId = event.target.getAttribute('data-band-id');
            action = event.target.getAttribute('data-action');
            targetButton = event.target;
        } 
        else if (event.target && event.target.matches('.remind-btn')) {
            bandId = event.target.getAttribute('data-band-id');
            action = 'remind_me';
            targetButton = event.target;
        }

        if (bandId && action) {
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
                    throw new Error('Failed to update band preference.');
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    if (action === 'like' || action === 'dislike') {
                        const likeBtn = document.querySelector(`.like-btn[data-band-id="${bandId}"][data-action="like"]`);
                        const dislikeBtn = document.querySelector(`.like-btn[data-band-id="${bandId}"][data-action="dislike"]`);

                        likeBtn.classList.remove('active');
                        likeBtn.classList.add('inactive');
                        dislikeBtn.classList.remove('active');
                        dislikeBtn.classList.add('inactive');

                        if (data.liked_state === true) {
                            likeBtn.classList.add('active');
                            likeBtn.classList.remove('inactive');
                        } else if (data.liked_state === false) {
                            dislikeBtn.classList.add('active');
                            dislikeBtn.classList.remove('inactive');
                        }

                    } else if (action === 'remind_me') {
                        if (data.remind_me_state === true) {
                            targetButton.classList.add('active');
                            targetButton.classList.remove('inactive');
                        } else {
                            targetButton.classList.remove('active');
                            targetButton.classList.add('inactive');
                        }
                    }
                } else {
                    console.error('Server reported an error:', data.message);
                }
            })
            .catch(error => {
                console.error('Error during fetch operation:', error);
                alert(`There was an error: ${error.message}`);
            });
        }
    });
}