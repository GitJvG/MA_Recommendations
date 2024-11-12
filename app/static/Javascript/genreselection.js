$(document).ready(function() {
    $.ajax({
        url: '/get_genres',
        method: 'GET',
        success: function(data) {
            data.forEach(function(genre) {
                $('#genre1').append(new Option(genre, genre));
                $('#genre2').append(new Option(genre, genre));
                $('#genre3').append(new Option(genre, genre));
            });

            // Initialize Select2
            $('#genre1, #genre2, #genre3').select2();
        }
    });
});