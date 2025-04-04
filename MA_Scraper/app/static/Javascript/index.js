import("/static/Javascript/renderalbums.js")
    .then(module => {
        const { loadData } = module;
        function refresh() {
            console.log('im doin something alr');
            loadData("/ajax/featured", ".featured-cards", "album",null,7);
            loadData("/ajax/recommended_albums", ".album-cards", "album",null,7);
            loadData("/ajax/remind", ".reminder-cards", "album",null,7);
            loadData("/ajax/known_albums", ".known_album-cards", "album",null,7);
        }

        console.log('im doin something alr2');
        refresh();
    })
    .catch(error => {
        console.error('Error loading the module:', error);
    });