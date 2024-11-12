$(document).ready(function() {
    $('.navbar-toggler').click(function() {
        var sidebar = $('#sidebar'); // Reference to the sidebar
        sidebar.toggleClass('expanded'); // Toggle expanded class

        if (sidebar.hasClass('expanded')) {
            sidebar.css('width', '15%'); // Expand to 15%
        } else {
            sidebar.css('width', '8%'); // Collapse to 8%
        }
    });
});
