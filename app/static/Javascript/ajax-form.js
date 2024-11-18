$(document).on('submit', 'form', function (e) {
    e.preventDefault(); // Prevent default form submission
    var form = $(this);
    var url = form.attr('action') || window.location.href;
    var method = form.attr('method') || 'POST';

    $.ajax({
        url: url,
        method: method,
        data: form.serialize(),
        success: function(response) {
            if (response.success) {
                if (response.pop_up) {
                    $('#notification').text(response.pop_up).addClass('show');
                    
                    setTimeout(function() {
                        $('#notification').removeClass('show');
                    }, 3000);  // 3 seconds
                }

                if (response.redirect_url) {
                    $('#sidebar').html(response.sidebar_html);
                }
                if (response.redirect_url) {
                    // Only try to load partial content if a redirect URL is provided
                    $.get(response.redirect_url, function(partialContent) {
                        $('#main-content').html(partialContent);

                        var newTitle = $(partialContent).filter('title').text();
                        if (newTitle) {
                            document.title = newTitle;
                        }
                    });
                }
            } else {
                // Handle error message returned from the server
                alert('Error: ' + response.error);
            }
        },
        error: function(xhr, status, error) {
            // Handle AJAX error (network issues, etc.)
            alert('An error occurred during the request.');
        }
    });
});
