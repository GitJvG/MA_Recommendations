$(document).ready(function() {
    // Fetch genres and user data from the server using AJAX
    $.ajax({
        url: '/get_genres',  // Your API endpoint to get the genres and user data
        method: 'GET',
        success: function(data) {
            // Populate the select elements with the fetched genres
            data.forEach(function(genre) {
                $('#genre1').append(new Option(genre, genre));
                $('#genre2').append(new Option(genre, genre));
                $('#genre3').append(new Option(genre, genre));
            });

            var genre1Selected = $('#genre1').data('selected');
            if (genre1Selected) {
                $('#genre1').val(genre1Selected).trigger('change');  // Trigger change to update Select2 if used
            }

            // For genre2
            var genre2Selected = $('#genre2').data('selected');
            if (genre2Selected) {
                $('#genre2').val(genre2Selected).trigger('change');
            }

            // For genre3
            var genre3Selected = $('#genre3').data('selected');
            if (genre3Selected) {
                $('#genre3').val(genre3Selected).trigger('change');
            }

            // Initialize the search feature for each select dropdown
            enableSearch('#genre1', '#genre1-search');
            enableSearch('#genre2', '#genre2-search');
            enableSearch('#genre3', '#genre3-search');
        }
    });
    // Function to enable search for each select dropdown
    function enableSearch(selectId, searchInputId) {
        $(searchInputId).on('input', function() {
            var searchValue = $(this).val().toLowerCase();
            $(selectId).find('option').each(function() {
                var optionText = $(this).text().toLowerCase();
                if (optionText.indexOf(searchValue) !== -1) {
                    $(this).show(); // Show options that match the search
                } else {
                    $(this).hide(); // Hide options that don't match the search
                }
            });
        });
    }
});
