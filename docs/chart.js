import { API_BASE_URL } from './config.js';

export async function loadChart() {
    return fetch('html/chart.html')
        .then(response => response.text())
        .then(data => {
            document.getElementById('chart-container').innerHTML = data;
        })
        .catch(error => {
            console.error('Error loading chart HTML:', error);
        });
}

async function loadChartJsLibrary() {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

export async function fetchAndDisplayChartData(genre, isrc) {
    await loadChart();  

    await loadChartJsLibrary(); 

    try {
        const response = await fetch(`${API_BASE_URL}/api/graph-data?genre=${genre}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch chart data. Status: ${response.status}`);
        }
        const data = await response.json();

        const trackData = data.find(track => track.isrc === isrc);
        if (trackData) {
            displayChart(trackData);
        } else {
            console.error('No data found for the provided ISRC:', isrc);
        }
    } catch (error) {
        console.error('Error fetching chart data:', error);
    }
}

function displayChart(track) {
    const ctx = document.getElementById('myChart').getContext('2d');

    // Sort the view counts based on the timestamp
    const sortedSpotifyViewCounts = track.view_counts.Spotify.sort((a, b) => new Date(a[0]) - new Date(b[0]));
    const sortedYoutubeViewCounts = track.view_counts.Youtube.sort((a, b) => new Date(a[0]) - new Date(b[0]));

    const labels = sortedYoutubeViewCounts.map(viewCount => new Date(viewCount[0]).toLocaleString('en-US', { 
        hour12: false, 
        timeZoneName: 'short'
    }));
    const spotifyData = sortedSpotifyViewCounts.map(viewCount => viewCount[1]);
    const youtubeData = sortedYoutubeViewCounts.map(viewCount => viewCount[1]);

    const albumCover = track.album_cover_url;

    const img = new Image();
    img.src = albumCover;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Spotify Views',
                    data: spotifyData,
                    borderColor: '#1DB954', 
                    fill: false,
                    pointRadius: 10,
                    pointBackgroundColor: '#1DB954' 
                },
                {
                    label: 'YouTube Views',
                    data: youtubeData,
                    borderColor: '#FF0000', 
                    fill: false,
                    pointRadius: 10,
                    pointBackgroundColor: '#FF0000'
                }
            ]
        },
        options: {
            plugins: {
                title: {
                    display: true,
                    text: `${track.track_name} by ${track.artist_name} - View Counts Received Over Time`
                },
                legend: {
                    display: true,
                    position: 'top',
                    align: 'end'
                },
                afterDraw: (chart) => {
                    const ctx = chart.ctx;
                    chart.data.datasets.forEach((dataset, datasetIndex) => {
                        dataset.data.forEach((value, index) => {
                            const point = chart.getDatasetMeta(datasetIndex).data[index];
                            if (img.complete) {
                                ctx.drawImage(img, point.x - 15, point.y - 30, 30, 30);
                            } else {
                                img.onload = () => {
                                    ctx.drawImage(img, point.x - 15, point.y - 30, 30, 30);
                                };
                            }
                        });
                    });
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}
