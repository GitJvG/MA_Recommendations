import { fetchContent } from './utils.js'

document.addEventListener('click', function (e) {
    let url = null;

    if (e.target.classList.contains('ajax-link')) {
        e.preventDefault();
        url = e.target.getAttribute('href');
    } else if (e.target.tagName === 'IMG' && e.target.parentElement.classList.contains('ajax-link')) {
        e.preventDefault();
        url = e.target.parentElement.getAttribute('href');
    }

    if (url) {
        fetchContent(url);
    }
});
