function displayResults(results) {
    const resultsContainer = document.getElementById('results-container');
    resultsContainer.innerHTML = ''; // Clear previous results

    // Display the success statistics at the top
    const successStats = document.createElement('div');
    successStats.classList.add('success-stats');
    successStats.innerHTML = `
        <p>Success Count: ${results.success_count}<br>
        Failure Count: ${results.failure_count}<br>
        Newly liked bands: ${results.newly_liked_count}</p>
    `;
    resultsContainer.appendChild(successStats);

    // Create the table structure
    const table = document.createElement('table');
    table.classList.add('results-table');

    // Add table headers
    const headerRow = document.createElement('tr');
    headerRow.innerHTML = `
        <th>Band Name</th>
        <th>Newly liked</th>
        <th>Video Titles</th>
    `;
    table.appendChild(headerRow);

    // Add rows for each result
    results.matches.forEach(group => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${group.band_id !== null ? `<a class="nav-link ajax-link" href="/band/${group.band_id}">${group.band_name}</a>` : 'No Band Found'}</td>
            <td>${group.new}</td>
            <td>${group.video_titles.join(', ')}</td>
        `;
        table.appendChild(row);
    });

    // Append the table to the container
    resultsContainer.appendChild(table);
}