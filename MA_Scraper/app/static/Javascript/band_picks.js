import("/static/Javascript/renderalbums.js")
    .then(module => {
        const { loadData } = module;
        function refresh() {
            const pathParts = window.location.pathname.split("/");
            const bandId = pathParts[pathParts.length - 1];
            loadData('/ajax/above_avg_albums', ".top_album-cards", "album", [bandId], 6);
        }

        refresh();
    })