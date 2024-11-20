function filter() {
    const discographyFilter = document.getElementById('discographyFilter');

    function filterDiscography() {
        const selectedTypes = Array.from(discographyFilter.selectedOptions).map(option => option.value) || [];
        if (selectedTypes.length === 0) {
            // Ensure 'all' is selected by default if neither of the two types is selected
            const allOption = discographyFilter.querySelector('option[value="all"]');
            if (allOption) {
                allOption.selected = true;
            }
            selectedTypes.push('all');  // Add 'all' to the selectedTypes array for filtering
        }
        const rows = document.querySelectorAll('#discographyTable tbody tr');
        
        rows.forEach(function (row) {
            const rowType = row.getAttribute('data-type');
            if (selectedTypes.includes('all') || selectedTypes.includes(rowType)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    discographyFilter.addEventListener('change', function () {
        filterDiscography();
    });

    filterDiscography();
};

filter()