function filter() {
    const discographyFilterBtn = document.getElementById('discographyFilterBtn');
    const dropdownMenu = document.getElementById('dropdownMenu');
    const checkboxes = dropdownMenu.querySelectorAll('input[type="checkbox"]');
    const filterTitle = document.getElementById('filterTitle');  // Reference to the title element

    // Function to toggle the dropdown visibility
    discographyFilterBtn.addEventListener('click', function () {
        dropdownMenu.classList.toggle('show');
    });

    // Function to filter discography based on selected types
    function filterDiscography() {
        const selectedTypes = Array.from(checkboxes)
            .filter(checkbox => checkbox.checked)
            .map(checkbox => checkbox.value);

        // Get the "All" checkbox and update its behavior
        const allCheckbox = dropdownMenu.querySelector('input[value="all"]');

        if (allCheckbox.checked) {
            // If "All" is checked, automatically deselect other checkboxes
            checkboxes.forEach(checkbox => {
                if (checkbox.value !== 'all') checkbox.checked = false;
            });
        } else if (selectedTypes.includes('all')) {
            // Remove "all" from selectedTypes if other checkboxes are selected
            const index = selectedTypes.indexOf('all');
            selectedTypes.splice(index, 1);
        }

        // Update the title to show the selected types
        updateTitle(selectedTypes);

        const rows = document.querySelectorAll('#discographyTable tbody tr');

        rows.forEach(function (row) {
            const rowType = row.getAttribute('data-type');
            if (
                selectedTypes.length === 0 || // If no specific type is selected
                selectedTypes.includes('all') || // 'All' is selected
                selectedTypes.includes(rowType) // Row matches selected type
            ) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    // Function to update the title text
    function updateTitle(selectedTypes) {
        if (selectedTypes.length === 0) {
            filterTitle.textContent = "Filtered: None";  // Display default message if no filter is selected
        } else {
            filterTitle.textContent = "Filtered: " + selectedTypes.join(", ");  // Display selected types as a comma-separated list
        }
    }

    // Add event listener to each checkbox for filtering
    checkboxes.forEach(function (checkbox) {
        checkbox.addEventListener('change', function() {
            // If "All" is clicked, handle it separately
            const allCheckbox = dropdownMenu.querySelector('input[value="all"]');
            if (checkbox.value === 'all') {
                if (checkbox.checked) {
                    // Select all checkboxes when "All" is selected
                    checkboxes.forEach(chk => {
                        if (chk !== checkbox) chk.checked = true;
                    });
                } else {
                    // If "All" is deselected, deselect all other checkboxes if nothing else is checked
                    if (Array.from(checkboxes).every(chk => chk !== checkbox && !chk.checked)) {
                        checkbox.checked = true;  // Re-select "All" if nothing else is selected
                    }
                }
            } else {
                // If any other checkbox is clicked, deselect "All"
                const allCheckbox = dropdownMenu.querySelector('input[value="all"]');
                allCheckbox.checked = false;
            }
            filterDiscography();  // Call filter function after checkbox change
        });
    });

    // Close dropdown if clicked outside
    document.addEventListener('click', function (event) {
        if (!event.target.closest('.custom-dropdown')) {
            dropdownMenu.classList.remove('show');
        }
    });

    filterDiscography();  // Apply the filter on load
}

filter();