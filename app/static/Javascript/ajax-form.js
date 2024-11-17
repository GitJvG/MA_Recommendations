// Handle login form submission via AJAX
$(document).on('submit', 'form', function (e) {
    e.preventDefault(); // Prevent default form submission
    var form = $(this);
    var url = form.attr('action') || window.location.href;
    var method = form.attr('method') || 'POST';

    // Submit the form via AJAX
    $.ajax({
        url: url,  // This points to the /login route
        method: method,  // POST method
        data: form.serialize(),  // Send form data
        success: function(response) {
            if (response.success) {
                // On successful login, refresh the sidebar
                $('#sidebar').html(response.sidebar_html);  // Replace the sidebar content

                // Optionally, replace the main content or other parts of the page
                $.get(response.redirect_url, function(partialContent) {
                    $('#main-content').html(partialContent);

                    // Optionally update the document title (e.g., to match the new page)
                    var newTitle = $(partialContent).filter('title').text();
                    if (newTitle) {
                        document.title = newTitle;
                    }
                });
            } else {
                alert('Login failed: ' + (response.error || 'Unknown error'));
            }
        },
        error: function(xhr) {
            alert('An error occurred during login.');
        }
    });
});