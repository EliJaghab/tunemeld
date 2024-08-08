document.addEventListener('DOMContentLoaded', initializeApp);

function initializeApp() {
  const genreSelector = document.getElementById('genre-selector');
  const viewCountTypeSelector = document.getElementById('view-count-type-selector');

  let currentGenre = genreSelector.value || 'pop';
  let viewCountType = viewCountTypeSelector.value || 'total-view-count';

  updateGenreData(currentGenre, viewCountType, true);

  setupGenreSelector(genreSelector);
  setupViewCountTypeSelector(viewCountTypeSelector);
  setupBodyClickListener();
  setupSortButtons();
  setupClosePlayerButton();
}

function setupGenreSelector(genreSelector) {
  genreSelector.addEventListener('change', function () {
    const currentGenre = genreSelector.value;
    updateGenreData(currentGenre, getCurrentViewCountType(), true);
  });
}

function setupViewCountTypeSelector(viewCountTypeSelector) {
  viewCountTypeSelector.addEventListener('change', function () {
    const viewCountType = viewCountTypeSelector.value;
    sortTable(getCurrentColumn(), getCurrentOrder(), viewCountType);
  });
}

function setupBodyClickListener() {
  const body = document.body;
  if (!body) {
    console.error("Body element not found.");
    return;
  }

  body.addEventListener('click', (event) => {
    const link = event.target.closest('a');
    if (link) {
      handleLinkClick(event, link);
    }
  });
}

function setupSortButtons() {
  document.querySelectorAll('.sort-button').forEach(button => {
    button.addEventListener('click', function () {
      const column = button.getAttribute('data-column');
      const order = button.getAttribute('data-order');
      const newOrder = order === 'desc' ? 'asc' : 'desc';
      button.setAttribute('data-order', newOrder);
      setCurrentColumn(column);
      setCurrentOrder(newOrder);
      sortTable(column, newOrder, getCurrentViewCountType());
    });
  });
}

function setupClosePlayerButton() {
  const closePlayerButton = document.getElementById('close-player-button');
  if (closePlayerButton) {
    closePlayerButton.addEventListener('click', closePlayer);
  } else {
    console.error("Close player button not found.");
  }
}

function handleLinkClick(event, link) {
  const url = link.href;
  console.log("Clicked URL:", url);
  let serviceType = 'none';

  if (isSoundCloudLink(url)) {
    serviceType = 'soundcloud';
  } else if (isSpotifyLink(url)) {
    serviceType = 'spotify';
  } else if (isAppleMusicLink(url)) {
    serviceType = 'applemusic';
  }

  console.log("Detected service type:", serviceType);

  if (serviceType !== 'none') {
    event.preventDefault();
    openPlayer(url, serviceType);
    
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  } else {
    console.log("No matching service type found, link will behave normally");
  }

  return serviceType;
}

function getCurrentViewCountType() {
  return document.getElementById('view-count-type-selector').value || 'total-view-count';
}

function getCurrentColumn() {
  return document.querySelector('.sort-button[data-order]').getAttribute('data-column') || 'rank';
}

function getCurrentOrder() {
  return document.querySelector('.sort-button[data-order]').getAttribute('data-order') || 'asc';
}

function setCurrentColumn(column) {
  document.querySelector('.sort-button[data-column]').setAttribute('data-column', column);
}

function setCurrentOrder(order) {
  document.querySelector('.sort-button[data-order]').setAttribute('data-order', order);
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

async function updateGenreData(genre, viewCountType, updateAll = false) {
  try {
    showSkeletonLoaders();
    if (updateAll) {
      await fetchAndDisplayLastUpdated(genre);
      await fetchAndDisplayHeaderArt(genre);
      await fetchAndDisplayPlaylists(genre);
    }
    await updateMainPlaylist(genre, viewCountType);
    sortTable('rank', 'asc', 'total-view-count');
    hideSkeletonLoaders();
    resetCollapseStates();
    addToggleEventListeners();
  } catch (error) {
    console.error('Error updating genre data:', error);
  }
}

async function updateMainPlaylist(genre, viewCountType) {
  try {
    const url = `${API_BASE_URL}/api/main-playlist?genre=${genre}`;
    await fetchAndDisplayData(url, 'main-playlist-data-placeholder', true, viewCountType);
  } catch (error) {
    console.error('Error updating main playlist:', error);
  }
}

async function fetchAndDisplayLastUpdated(genre) {
  const url = `${API_BASE_URL}/api/last-updated?genre=${genre}`;
  await fetchAndDisplayData(url, 'last-updated');
}

async function fetchAndDisplayHeaderArt(genre) {
  const url = `${API_BASE_URL}/api/header-art?genre=${genre}`;
  await fetchAndDisplayData(url, 'header-art');
}

async function fetchAndDisplayPlaylists(genre) {
  const services = ['AppleMusic', 'SoundCloud', 'Spotify'];
  for (const service of services) {
    await fetchAndDisplayData(`${API_BASE_URL}/api/service-playlist?genre=${genre}&service=${service}`, `${service.toLowerCase()}-data-placeholder`);
  }
}
