function like() {
    const likeButtons = document.querySelectorAll('.like-btn');
    likeButtons.forEach(button => {
        button.addEventListener('click', function () {
            const bandId = this.getAttribute('data-band-id');
            const action = this.getAttribute('data-action');
            console.log(`Band ID: ${bandId}, Action: ${action}`);

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
                console.log('Response:', data);

                if (data.status === 'success') {
                    document.querySelectorAll(`.like-btn[data-band-id="${bandId}"]`).forEach(btn => {
                        btn.classList.remove('disabled');
                        if (btn.getAttribute('data-action') === action) {
                            btn.classList.add('disabled');
                        }
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
}

like()