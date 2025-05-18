import("/static/Javascript/renderalbums.js")
    .then(module => {
        const { loadData } = module;
        function refresh() {
            const pathParts = window.location.pathname.split("/");
            const bandId = pathParts[pathParts.length - 1];
            loadData('/ajax/top_albums', ".top_album-cards", "album", [bandId], 6);
        }

        refresh();
    })