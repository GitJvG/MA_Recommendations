$(document).on('click', '.ajax-link', function (e) {
    e.preventDefault(); // Prevent default browser navigation
    var url = $(this).attr('href'); // Get the URL from the link's href attribute

    // Make an AJAX request to the server
    $.ajax({
        url: url,
        method: 'GET',
        success: function(response) {
            // Check if the response includes 'logout' in the URL or some identifier
            if (url.includes("logout")) {
                $('#sidebar').html(response.sidebar_html);
                $('#main-content').html(response.main_content_html);
            } else {
                // Otherwise, replace the main content with the response
                $('#main-content').html(response);

                // Optionally, update the document title (if the response has a title tag)
                var newTitle = $(response).filter('title').text();
                if (newTitle) {
                    document.title = newTitle;
                }
            }

            // Update the browser's URL without reloading the page
            history.pushState({ path: url }, '', url);
        },
        error: function(xhr, status, error) {
            console.error('Failed to load page: ', error);
            alert('An error occurred while loading the page.');
        }
    });
});

function updateSidebar() {
    $.ajax({
        url: '/get_sidebar', // URL to fetch updated sidebar
        method: 'GET',
        success: function(response) {
            $('#sidebar').html($(response).find('#sidebar').html());
        },
        error: function(xhr, status, error) {
            console.error('Failed to load sidebar: ', error);
        }
    });
}

