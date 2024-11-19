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
        .then(response => {
            if (response.success) {
                if (response.pop_up) {

                    var notification = document.getElementById('notification');
                    notification.textContent = response.pop_up;
                    notification.classList.add('show');

                    // Hide notification after 3 seconds
                    setTimeout(function () {
                        notification.classList.remove('show');
                    }, 3000); // 3 seconds
                }

                if (response.redirect_url) {
                    if (response.sidebar_html) {
                        document.getElementById('sidebar').innerHTML = response.sidebar_html;
                    }

                    fetch(response.redirect_url, {
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    })
                        .then(partialResponse => {
                            if (!partialResponse.ok) {
                                throw new Error(`HTTP error! status: ${partialResponse.status}`);
                            }
                            return partialResponse.text();
                        })
                        .then(partialContent => {
                            document.getElementById('main-content').innerHTML = partialContent;

                            var parser = new DOMParser();
                            var doc = parser.parseFromString(partialContent, 'text/html');
                            var newTitle = doc.querySelector('title');
                            if (newTitle) {
                                document.title = newTitle.textContent;
                            }
                        });
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
