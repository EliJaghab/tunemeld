import { DJANGO_API_BASE_URL } from "@/config/config.js";

let currentChart = null;

async function loadChart() {
  try {
    const response = await fetch("html/chart.html");
    const data = await response.text();
    document.getElementById("chart-container").innerHTML = data;
  } catch (error) {
    console.error("Error loading chart HTML:", error);
  }
}

async function loadChartJsLibrary() {
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/chart.js";
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

async function fetchChartData(genre, isrc) {
  try {
    const response = await fetch(`${DJANGO_API_BASE_URL}/graph-data/${genre}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch chart data. Status: ${response.status}`);
    }
    const responseData = await response.json();
    const data = responseData.data || responseData;
    const trackData = data.find((track) => track.isrc === isrc);
    if (!trackData) {
      console.error("No data found for the provided ISRC:", isrc);
      return null;
    }
    return trackData;
  } catch (error) {
    console.error("Error fetching chart data:", error);
    return null;
  }
}

function sortViewCounts(viewCounts) {
  return viewCounts.sort((a, b) => new Date(a[0]) - new Date(b[0]));
}

function prepareChartData(track) {
  const sortedSpotifyViewCounts = sortViewCounts(track.view_counts.Spotify);
  const sortedYoutubeViewCounts = sortViewCounts(track.view_counts.Youtube);

  const labels = sortedYoutubeViewCounts.map((viewCount) =>
    new Date(viewCount[0]).toLocaleDateString("en-US", {
      month: "numeric",
      day: "numeric",
      year: "2-digit",
    }),
  );
  const spotifyData = sortedSpotifyViewCounts.map((viewCount) => viewCount[1]);
  const youtubeData = sortedYoutubeViewCounts.map((viewCount) => viewCount[1]);

  return {
    labels,
    spotifyData,
    youtubeData,
    albumCover: track.album_cover_url,
  };
}

function displayChart(track) {
  const ctx = document.getElementById("myChart").getContext("2d");

  if (currentChart) {
    currentChart.destroy();
  }

  const { labels, spotifyData, youtubeData, albumCover } =
    prepareChartData(track);
  const img = new Image();
  img.src = albumCover;

  currentChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Spotify Views",
          data: spotifyData,
          borderColor: "#1DB954",
          fill: false,
          pointRadius: 3,
          pointBackgroundColor: "#1DB954",
        },
        {
          label: "YouTube Views",
          data: youtubeData,
          borderColor: "#FF0000",
          fill: false,
          pointRadius: 3,
          pointBackgroundColor: "#FF0000",
        },
      ],
    },
    options: {
      plugins: {
        title: {
          display: true,
          text: `${track.track_name} by ${track.artist_name} - View Counts Received Over Time`,
        },
        legend: {
          display: true,
          position: "top",
          align: "end",
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
        },
      },
      scales: {
        y: {
          type: "logarithmic",
          beginAtZero: true,
          ticks: {
            callback: function (value) {
              return Number(value.toString());
            },
            maxTicksLimit: 10,
          },
          title: {
            display: true,
            text: "Logarithmic Scale",
          },
        },
      },
    },
  });
}

export async function fetchAndDisplayChartData(genre, isrc) {
  await loadChart();
  await loadChartJsLibrary();

  const trackData = await fetchChartData(genre, isrc);
  const chartContainer = document.getElementById("chart-container");

  if (trackData) {
    displayChart(trackData);
    chartContainer.classList.add("show");
  } else {
    chartContainer.classList.remove("show");
  }
}

export function hideChart() {
  const chartContainer = document.getElementById("chart-container");
  if (chartContainer) {
    chartContainer.classList.remove("show");
  }
}
