import { fetchContent } from './utils.js'

if (!window.AjaxDefListenerAdded) {
    window.AjaxDefListenerAdded = true;
    document.addEventListener('click', function (e) {
        const link = e.target.closest('a.ajax-link');

        if (link) {
            e.preventDefault();
            const url = link.getAttribute('href');
            fetchContent(url);
        }
    });
}

if (!window.PopstateListenerAdded) {
    window.PopstateListenerAdded = true;
    window.addEventListener('popstate', (e) => {
        if (e.state && e.state.path) {
            fetchContent(e.state.path, true);
        }
    });
}