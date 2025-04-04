fetch('/get_genres')
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Check if the response is an array, since it seems to be just an array of genres
        if (Array.isArray(data)) {
            data.forEach(function (genre) {
                document.querySelectorAll('#genre1, #genre2, #genre3').forEach(select => {
                    const option = new Option(genre, genre);
                    select.appendChild(option);
                });
            });

            setSelectedValue('genre1');
            setSelectedValue('genre2');
            setSelectedValue('genre3');

            enableSearch('genre1', 'genre1-search');
            enableSearch('genre2', 'genre2-search');
            enableSearch('genre3', 'genre3-search');
        } else {
            console.error('Genres data is not an array or is missing:', data);
        }
    })
    .catch(error => {
        console.error('Error fetching genres:', error);
    });

function setSelectedValue(selectId) {
    const selectElement = document.getElementById(selectId);
    const selectedValue = selectElement.dataset.selected;
    if (selectedValue) {
        selectElement.value = selectedValue;
        const event = new Event('change');
        selectElement.dispatchEvent(event);
    }
}

function enableSearch(selectId, searchInputId) {
    const searchInput = document.getElementById(searchInputId);
    const selectElement = document.getElementById(selectId);

    if (searchInput && selectElement) {
        searchInput.addEventListener('input', function () {
            const searchValue = searchInput.value.toLowerCase();
            Array.from(selectElement.options).forEach(option => {
                const optionText = option.text.toLowerCase();
                option.style.display = optionText.includes(searchValue) ? '' : 'none';
            });
        });
    }
}
