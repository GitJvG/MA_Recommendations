function like() {
    const likeButtons = document.querySelectorAll('.like-btn');
    const remindButtons = document.querySelectorAll('.remind-btn');

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
                    throw new Error('Failed to like/dislike/remind me band.');
                }
                return response.json();
            })
            .then(data => {
                console.log('Response:', data);

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
        });
    });

    remindButtons.forEach(button => {
        button.addEventListener('click', function () {
            const bandId = this.getAttribute('data-band-id');
            const action = 'remind_me';

            console.log(`Band ID: ${bandId}, Remind Me state triggered`);

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
                console.log('Remind Me state updated:', data);
                const currentState = this.classList.contains('active') ? 'active' : 'inactive';
                const newState = currentState === 'active' ? 'inactive' : 'active';

                this.classList.remove(currentState);
                this.classList.add(newState);
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
}

like();
