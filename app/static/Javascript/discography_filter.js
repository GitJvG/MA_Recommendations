function filter() {
    const discographyFilterBtn = document.getElementById('discographyFilterBtn');
    const dropdownMenu = document.getElementById('dropdownMenu');
    const checkboxes = dropdownMenu.querySelectorAll('input[type="checkbox"]');

    // Function to toggle the dropdown visibility
    discographyFilterBtn.addEventListener('click', function() {
        dropdownMenu.classList.toggle('show');  // Toggle dropdown visibility
    });

    // Function to filter discography based on selected types
    function filterDiscography() {
        const selectedTypes = Array.from(checkboxes)
            .filter(checkbox => checkbox.checked)
            .map(checkbox => checkbox.value);

        if (selectedTypes.length === 0) {
            // Ensure 'all' is selected by default if neither of the two types is selected
            selectedTypes.push('all');
        }

        const rows = document.querySelectorAll('#discographyTable tbody tr');
        
        rows.forEach(function(row) {
            const rowType = row.getAttribute('data-type');
            if (selectedTypes.includes('all') || selectedTypes.includes(rowType)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    // Add event listener to each checkbox for filtering
    checkboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', filterDiscography);
    });

    // Close dropdown if clicked outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.custom-dropdown')) {
            dropdownMenu.classList.remove('show');
        }
    });

    filterDiscography();  // Apply the filter on load
}

filter();