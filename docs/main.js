document.addEventListener('DOMContentLoaded', function () {
  fetchAndDisplayLastUpdated();
  initializePlaylists('rap'); // Initially load 'rap' genre, as selected in the dropdown

  document.getElementById('genre-selector').addEventListener('change', function (event) {
    initializePlaylists(event.target.value);
  });
});

const API_BASE_URL = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' 
  ? 'http://127.0.0.1:8787' 
  : 'your-production-url';

async function fetchAndDisplayLastUpdated() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/last-updated`);
    if (!response.ok) {
      throw new Error(`Failed to fetch last-updated. Status: ${response.status}`);
    }
    const lastUpdated = await response.json();
    const lastUpdatedDate = new Date(lastUpdated.lastUpdated);
    const formattedDate = lastUpdatedDate.toLocaleString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      timeZoneName: 'short',
    });
    document.getElementById('last-updated').textContent = `Last Updated - ${formattedDate}`;
  } catch (error) {
    console.error('Error fetching last updated date:', error);
  }
}

async function initializePlaylists(genre) {
  try {
    await fetchAndDisplayData(`${API_BASE_URL}/api/transformed-playlist?genre=${genre}&service=AppleMusic`, 'apple-music-data-placeholder');
    await fetchAndDisplayData(`${API_BASE_URL}/api/transformed-playlist?genre=${genre}&service=SoundCloud`, 'soundcloud-data-placeholder');
    await fetchAndDisplayData(`${API_BASE_URL}/api/transformed-playlist?genre=${genre}&service=Spotify`, 'spotify-data-placeholder');
    await fetchAndDisplayData(`${API_BASE_URL}/api/aggregated-playlist?genre=${genre}`, 'aggregated-data-placeholder', true);
  } catch (error) {
    console.error('Error initializing playlists:', error);
  }
}

async function fetchAndDisplayData(url, placeholderId, isAggregated = false) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch ${url}. Status: ${response.status}`);
    }
    const data = await response.json();
    displayData(data, placeholderId, isAggregated);
  } catch (error) {
    console.error('Error fetching and displaying data:', error);
  }
}

function displayData(data, placeholderId, isAggregated = false) {
  const placeholder = document.getElementById(placeholderId);
  if (!placeholder) {
    console.error(`Placeholder with ID ${placeholderId} not found.`);
    return;
  }
  placeholder.innerHTML = '';
  data.forEach((playlist) => {
    playlist.tracks.forEach((track) => {
      const card = createCard(track, isAggregated);
      placeholder.appendChild(card);
    });
  });
}

function createCard(track, isAggregated) {
  const card = document.createElement('div');
  card.className = 'card my-1';
  const cardBody = document.createElement('div');
  cardBody.className = 'card-body track-item-content';

  const trackNumber = document.createElement('div');
  trackNumber.className = 'track-number';
  trackNumber.textContent = track.rank || '';

  const albumCover = document.createElement('img');
  albumCover.className = 'album-cover';
  albumCover.src = track.album_cover_url || ''; // Ensure the URL is not undefined
  albumCover.alt = 'Album Cover';

  const trackInfo = document.createElement('div');
  trackInfo.className = 'track-info';
  const trackTitle = document.createElement('a');
  trackTitle.className = 'track-title';
  trackTitle.href = track.track_url || '#'; // Ensure the URL is not undefined
  trackTitle.textContent = track.track_name || 'Unknown Track';

  const artistNameElement = document.createElement('span');
  artistNameElement.className = 'artist-name';
  artistNameElement.textContent = track.artist_name || 'Unknown Artist';

  trackInfo.appendChild(trackTitle);
  trackInfo.appendChild(document.createElement('br'));
  trackInfo.appendChild(artistNameElement);

  cardBody.appendChild(trackNumber);
  cardBody.appendChild(albumCover);
  cardBody.appendChild(trackInfo);

  if (isAggregated) {
    const seenOnColumn = document.createElement('div');
    seenOnColumn.className = 'track-column source-icons';
    displaySources(seenOnColumn, track);
    cardBody.appendChild(seenOnColumn);
  }

  const externalLinksColumn = document.createElement('div');
  externalLinksColumn.className = 'track-column external-links';
  if (track.youtube_url) {
    const youtubeLink = createSourceLink('youtube', track.youtube_url);
    externalLinksColumn.appendChild(youtubeLink);
  }

  cardBody.appendChild(externalLinksColumn);
  card.appendChild(cardBody);
  return card;
}

function displaySources(cardBody, track) {
  const sourcesContainer = document.createElement('div');
  sourcesContainer.className = 'track-sources';
  const allSources = {
    ...track.additional_sources,
    [track.source_name]: track.track_url,
  };
  Object.keys(allSources).forEach((source) => {
    const sourceLink = allSources[source];
    const linkElement = createSourceLink(source, sourceLink);
    sourcesContainer.appendChild(linkElement);
  });
  cardBody.appendChild(sourcesContainer);
}

function createSourceLink(source, sourceLink) {
  if (!sourceLink) {
    console.warn(`No Link available for source: ${source}`);
    return document.createTextNode('');
  }

  const sourceIcon = document.createElement('img');
  const linkElement = document.createElement('a');
  linkElement.href = sourceLink;
  linkElement.target = '_blank';
  sourceIcon.className = 'source-icon';
  switch (source) {
    case 'SoundCloud':
      sourceIcon.src = 'images/soundcloud_logo.png'; 
      sourceIcon.alt = 'SoundCloud';
      break;
    case 'Spotify':
      sourceIcon.src = 'images/spotify_logo.png';
      sourceIcon.alt = 'Spotify';
      break;
    case 'AppleMusic':
      sourceIcon.src = 'images/apple_music_logo.png'; 
      sourceIcon.alt = 'Apple Music';
      break;
    case 'YouTube':
      sourceIcon.src = 'images/youtube_logo.png';
      sourceIcon.alt = 'YouTube';
      break;
    default:
      console.log(source)
      return document.createTextNode(''); 
  }
  linkElement.appendChild(sourceIcon);
  return linkElement;
}
