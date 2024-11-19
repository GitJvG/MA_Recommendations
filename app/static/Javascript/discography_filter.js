document.addEventListener('DOMContentLoaded', function () {
    const discographyFilter = document.getElementById('discographyFilter');

    function filterDiscography() {
        const selectedTypes = Array.from(discographyFilter.selectedOptions).map(option => option.value) || [];

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
});
