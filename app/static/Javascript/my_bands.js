$(document).ready(function() {
    console.log("my_bands.js script is being executed.");
    const bandData = window.bandData;

    if (!Array.isArray(bandData)) {
        console.error("Invalid band data:", bandData);
        return;
    }

    const bandList = document.getElementById("band-list");

    // Loop through each band and generate the corresponding list item
    bandData.forEach(band => {
        const li = document.createElement('li');
        li.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
        li.innerHTML = `
            <div>
                <strong>${band.name}</strong>
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

    // Add click event listeners to buttons
    document.querySelectorAll('.like-btn').forEach(button => {
        button.addEventListener('click', function() {
            const bandId = this.getAttribute('data-band-id');
            const action = this.getAttribute('data-action');
            console.log(`Band ID: ${bandId}, Action: ${action}`);
            // Add logic for liking/disliking a band here
        });
    });
});
