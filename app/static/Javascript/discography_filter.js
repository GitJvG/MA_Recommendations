$(document).ready(function () {
    // Initialize Bootstrap Select
    $('#discographyFilter').selectpicker();

    // Function to filter the table based on the selected types
    function filterDiscography() {
        var selectedTypes = $('#discographyFilter').val() || [];
        $('#discographyTable tbody tr').each(function () {
            var rowType = $(this).data('type');
            if (selectedTypes.includes('all') || selectedTypes.includes(rowType)) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    }

    // Apply filter on change
    $('#discographyFilter').change(function () {
        filterDiscography();
    });

    // Trigger filter on page load to show default selection
    filterDiscography();
});
