import { fetchContent } from './utils.js'

document.addEventListener('click', function (e) {
    const link = e.target.closest('a.ajax-link');

    if (link) {
        e.preventDefault();
        const url = link.getAttribute('href');
        fetchContent(url);
    }
});

window.addEventListener('popstate', (e) => {
    if (e.state && e.state.path) {
        fetchContent(e.state.path, true);
    }
});