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

    const labels = track.view_counts.Youtube.map(viewCount => new Date(viewCount[0]).toLocaleDateString());
    const spotifyData = track.view_counts.Spotify.map(viewCount => viewCount[1]);
    const youtubeData = track.view_counts.Youtube.map(viewCount => viewCount[1]);

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
                    borderColor: 'rgba(75, 192, 192, 1)',
                    fill: false,
                    pointRadius: 10,
                    pointBackgroundColor: 'rgba(75, 192, 192, 1)'
                },
                {
                    label: 'YouTube Views',
                    data: youtubeData,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    fill: false,
                    pointRadius: 10,
                    pointBackgroundColor: 'rgba(255, 99, 132, 1)'
                }
            ]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
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
            }
        }
    });
}
