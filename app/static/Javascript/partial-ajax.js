import { fetchContent } from './utils.js'

document.addEventListener('click', function (e) {
    if (e.target.classList.contains('ajax-link')) {
        e.preventDefault();
        var url = e.target.getAttribute('href');
        fetchContent(url)}})