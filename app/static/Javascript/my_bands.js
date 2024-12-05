fetch('/feedback/ajax')
    .then(response => {
        if (!response.ok) {
            throw new Error("Failed to fetch band data");
        }
        return response.json();
    })
    .then(bandData => {
        if (!Array.isArray(bandData)) {
            console.error("Invalid band data:", bandData);
            return;
        }

        // Get today's date in the format "YYYY-MM-DD" for easy comparison
        const today = new Date().toISOString().split('T')[0];

        const bandList = document.getElementById("band-list");
        const todayBandList = document.getElementById("today-band-list");

        bandList.innerHTML = "";
        todayBandList.innerHTML = "";

        let interactedToday = [];
        let interactedBeforeToday = [];

        bandData.forEach(band => {
            const likedDate = band.liked_date ? new Date(band.liked_date).toISOString().split('T')[0] : null;

            const li = document.createElement('li');
            li.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
            li.innerHTML = create_like_dislike(band);

            if (likedDate === today) {
                interactedToday.push(li);
            } else {
                interactedBeforeToday.push(li);
            }
        });

        // Add the "interacted today" items first
        if (interactedToday.length > 0) {
            interactedToday.forEach(item => {
                todayBandList.appendChild(item);
            });
        } else {
            todayBandList.innerHTML = "<li class='list-group-item'>No interactions today.</li>";
        }

        // Add the "interacted before today" items
        interactedBeforeToday.forEach(item => {
            bandList.appendChild(item);
        });

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