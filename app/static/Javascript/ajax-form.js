import { fetchContent } from "./utils.js";

document.addEventListener('submit', function (e) {
    if (e.target.tagName === 'FORM') {
        e.preventDefault();

        var form = e.target;
        var url = form.action || window.location.href;
        var method = form.method || 'POST';
        var formData = new FormData(form);

        fetch(url, {
            method: method,
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        // If a pop-up was passed, show it temporarily upon submitting
        .then(response => {
            if (response.success) {
                if (response.pop_up) {

                    var notification = document.getElementById('notification');
                    notification.textContent = response.pop_up;
                    notification.classList.add('show');

                    setTimeout(function () {
                        notification.classList.remove('show');
                    }, 3000);
                }
                // If a redirect url was passed, redirect using ajax and refresh sidebar.
                if (response.redirect_url) {
                    if (response.sidebar_html) {
                        document.getElementById('sidebar').innerHTML = response.sidebar_html;
                    }

                    fetchContent(response.redirect_url)
                }
            } else {
                alert('Error: ' + response.error);
            }
        })
        .catch(error => {
            alert('An error occurred during the request: ' + error.message);
        });
    }
});
