function filter() {
    const discographyFilterBtn = document.getElementById('discographyFilterBtn');
    const dropdownMenu = document.getElementById('dropdownMenu');
    const checkboxes = dropdownMenu.querySelectorAll('input[type="checkbox"]');
    const filterTitle = document.getElementById('filterTitle');

    discographyFilterBtn.addEventListener('click', function () {
        dropdownMenu.classList.toggle('show');
    });

    function filterDiscography() {
        const selectedTypes = Array.from(checkboxes)
            .filter(checkbox => checkbox.checked)
            .map(checkbox => checkbox.value);

        const allCheckbox = dropdownMenu.querySelector('input[value="All"]');

        if (allCheckbox.checked) {
            checkboxes.forEach(checkbox => {
                if (checkbox.value !== 'All') checkbox.checked = false;
            });
        } else if (selectedTypes.includes('All')) {
            const index = selectedTypes.indexOf('All');
            selectedTypes.splice(index, 1);
        }

        updateTitle(selectedTypes);

        const rows = document.querySelectorAll('#discographyTable tbody tr');

        rows.forEach(function (row) {
            const rowType = row.getAttribute('data-type');
            if (
                selectedTypes.length === 0 ||
                selectedTypes.includes('All') ||
                selectedTypes.includes(rowType)
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
            filterTitle.textContent = "All";  // Display default message if no filter is selected
        } else {
            filterTitle.textContent = selectedTypes.join(", ");  // Display selected types as a comma-separated list
        }
    }

    // Add event listener to each checkbox for filtering
    checkboxes.forEach(function (checkbox) {
        checkbox.addEventListener('change', function() {
            const allCheckbox = dropdownMenu.querySelector('input[value="All"]');
            if (checkbox.value === 'All') {
                if (checkbox.checked) {
                    checkboxes.forEach(chk => {
                        if (chk !== checkbox) chk.checked = true;
                    });
                } else {
                    if (Array.from(checkboxes).every(chk => chk !== checkbox && !chk.checked)) {
                        checkbox.checked = true;
                    }
                }
            } else {
                const allCheckbox = dropdownMenu.querySelector('input[value="All"]');
                allCheckbox.checked = false;
            }
            filterDiscography();
        });
    });

    document.addEventListener('click', function (event) {
        if (!event.target.closest('.custom-dropdown')) {
            dropdownMenu.classList.remove('show');
        }
    });

    filterDiscography();
}

filter();