document.addEventListener('DOMContentLoaded', initializeApp);

function initializeApp() {
  const genreSelector = document.getElementById('genre-selector');
  const initialGenre = genreSelector.value;
  updateGenreData(initialGenre);

  genreSelector.addEventListener('change', function (event) {
    const selectedGenre = event.target.value;
    updateGenreData(selectedGenre);
  });
}

const useProdBackend = true;

function getApiBaseUrl() {
  if (useProdBackend) {
    return 'https://tunemeld.com';
  }
  
  return window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost'
    ? 'http://127.0.0.1:8787'
    : 'https://tunemeld.com';
}

const API_BASE_URL = getApiBaseUrl();

async function updateGenreData(genre) {
  try {
    await fetchAndDisplayLastUpdated(genre);
    await fetchAndDisplayHeaderArt(genre);
    await fetchAndDisplayPlaylists(genre);
  } catch (error) {
    console.error('Error updating genre data:', error);
  }
}
