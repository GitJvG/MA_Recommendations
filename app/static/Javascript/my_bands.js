fetch('/my_bands/ajax')
    .then(response => {
        if (!response.ok) {
            throw new Error("Failed to fetch band data");
        }
        return response.json();  // Parse the JSON response
    })
    .then(bandData => {
        if (!Array.isArray(bandData)) {
            console.error("Invalid band data:", bandData);
            return;
        }

        const bandList = document.getElementById("band-list");

        bandData.forEach(band => {
            const li = document.createElement('li');
            li.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
            
            li.innerHTML = `
                <div>
                    <a class="nav-link ajax-link" href="/band/${band.band_id}">${band.name}</a>
                    <p>Status: ${band.liked === true ? 'Liked' : 'Not Liked'}</p>
                </div>
                <div>
                    <button class="btn btn-success btn-sm like-btn ${band.liked ? 'disabled' : ''}" 
                            data-band-id="${band.band_id}" 
                            data-action="like" ${band.liked ? 'disabled' : ''}>
                        Like
                    </button>
                    <button class="btn btn-danger btn-sm like-btn ${!band.liked ? 'disabled' : ''}" 
                            data-band-id="${band.band_id}" 
                            data-action="dislike" ${!band.liked ? 'disabled' : ''}>
                        Dislike
                    </button>
                </div>
            `;

            bandList.appendChild(li);
        });

        // Add event listeners to like/dislike buttons
        const likeButtons = document.querySelectorAll('.like-btn');
        likeButtons.forEach(button => {
            button.addEventListener('click', function () {
                const bandId = this.getAttribute('data-band-id');
                const action = this.getAttribute('data-action');
                console.log(`Band ID: ${bandId}, Action: ${action}`);
            });
        });
    })
    .catch(error => {
        console.error("Error loading band data:", error);
    });