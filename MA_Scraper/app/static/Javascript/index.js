import("/static/Javascript/renderalbums.js")
    .then(module => {
        const { loadData } = module;
        function refresh() {
            loadData("/ajax/featured", ".featured-cards", "album",null,6);
            loadData("/ajax/recommended_albums", ".album-cards", "album",null,6);
            loadData("/ajax/remind", ".reminder-cards", "album",null,6);
            loadData("/ajax/known_albums", ".known_album-cards", "album",null,6);
        }
        refresh();
    })
    .catch(error => {
        console.error('Error loading the module:', error);
    });