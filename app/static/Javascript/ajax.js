$(document).ready(function () {
    // Store the initial scroll position
    var scrollPosition;

    $('.like-band').on('click', function () {
        // Save the current scroll position before the AJAX request
        scrollPosition = $(window).scrollTop();

        // Get the band ID and action from the button
        var bandId = $(this).data('band-id');
        var action = $(this).data('action');
        var $bandItem = $(this).closest('.list-group-item');

        // Send the AJAX request
        $.ajax({
            url: '/like_band',
            type: 'POST',
            data: {
                band_id: bandId,
                action: action
            },
            success: function (response) {

                // Restore scroll position after the request
                $(window).scrollTop(scrollPosition);
                $bandItem.remove();
            },
            error: function (error) {
                alert("An error occurred while saving your preference: " + (error.responseJSON.error || "Unknown error"));

                // Restore scroll position even on error (Mixed feelings)
                $(window).scrollTop(scrollPosition);
            }
        });
    });
});
