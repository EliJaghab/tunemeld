import { API_BASE_URL } from './config.js';
import { getCurrentViewCountType, setCurrentColumn, setCurrentOrder } from './selectors.js';

export async function fetchAndDisplayLastUpdated(genre) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/last-updated?genre=${genre}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch last-updated. Status: ${response.status}`);
    }
    const lastUpdated = await response.json();
    displayLastUpdated(lastUpdated);
  } catch (error) {
    console.error('Error fetching last updated date:', error);
  }
}

function displayLastUpdated(lastUpdated) {
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
}

export function setupSortButtons() {
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

export async function updateMainPlaylist(genre, viewCountType) {
  try {
    const url = `${API_BASE_URL}/api/main-playlist?genre=${genre}`;
    await fetchAndDisplayData(url, 'main-playlist-data-placeholder', true, viewCountType);
  } catch (error) {
    console.error('Error updating main playlist:', error);
  }
}

export async function fetchAndDisplayPlaylists(genre) {
  const services = ['AppleMusic', 'SoundCloud', 'Spotify'];
  for (const service of services) {
    await fetchAndDisplayData(`${API_BASE_URL}/api/service-playlist?genre=${genre}&service=${service}`, `${service.toLowerCase()}-data-placeholder`);
  }
}

async function fetchAndDisplayData(url, placeholderId, isAggregated = false, viewCountType) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch ${url}. Status: ${response.status}`);
    }
    const data = await response.json();
    playlistData = data;
    displayData(data, placeholderId, isAggregated, viewCountType);
  } catch (error) {
    console.error('Error fetching and displaying data:', error);
  }
}


function displayData(data, placeholderId, isAggregated = false, viewCountType) {
  
  const placeholder = document.getElementById(placeholderId);
  if (!placeholder) {
    console.error(`Placeholder with ID ${placeholderId} not found.`);
    return;
  }
  placeholder.innerHTML = '';
  data.forEach(playlist => {
    playlist.tracks.forEach(track => {
      const row = isAggregated ? createTableRow(track, isAggregated, viewCountType) : createSmallPlaylistTableRow(track);
      placeholder.appendChild(row);
    });
  });
}

function createTableRow(track, isAggregated, viewCountType) {  
  const row = document.createElement('tr');

  row.setAttribute('data-isrc', track.isrc);
  
  const rankCell = document.createElement('td');
  rankCell.className = 'rank';
  rankCell.textContent = track.rank;

  const coverCell = document.createElement('td');
  coverCell.className = 'cover';
  const albumCover = document.createElement('img');
  albumCover.className = 'album-cover';
  albumCover.src = track.album_cover_url || '';
  albumCover.alt = 'Album Cover';
  coverCell.appendChild(albumCover);

  const trackInfoCell = document.createElement('td');
  trackInfoCell.className = 'info';
  const trackInfoDiv = document.createElement('div');
  trackInfoDiv.className = 'track-info-div';

  const trackTitle = document.createElement('a');
  trackTitle.className = 'track-title';
  trackTitle.href = track.youtube_url || '#';
  trackTitle.textContent = track.track_name || 'Unknown Track';

  const artistNameElement = document.createElement('span');
  artistNameElement.className = 'artist-name';
  artistNameElement.textContent = track.artist_name || 'Unknown Artist';

  trackInfoDiv.appendChild(trackTitle);
  trackInfoDiv.appendChild(document.createElement('br'));
  trackInfoDiv.appendChild(artistNameElement);

  trackInfoCell.appendChild(trackInfoDiv);

  const youtubeStatCell = document.createElement('td');
  youtubeStatCell.className = 'youtube-view-count';
  youtubeStatCell.textContent = track.view_count_data_json.Youtube.current_count_json.current_view_count.toLocaleString()

  const spotifyStatCell = document.createElement('td');
  spotifyStatCell.className = 'spotify-view-count';
  spotifyStatCell.textContent = track.view_count_data_json.Spotify.current_count_json.current_view_count.toLocaleString()
  
  const seenOnCell = document.createElement('td');
  seenOnCell.className = 'seen-on';
  if (isAggregated) {
    displaySources(seenOnCell, track);
  }

  const externalLinksCell = document.createElement('td');
  externalLinksCell.className = 'external';
  if (track.youtube_url) {
    const youtubeLink = createSourceLink('YouTube', track.youtube_url);
    externalLinksCell.appendChild(youtubeLink);
  }

  row.appendChild(rankCell);
  row.appendChild(coverCell);
  row.appendChild(trackInfoCell);
  if (isAggregated) {
    displayViewCounts(track, row, viewCountType)
  }
  row.appendChild(seenOnCell);
  row.appendChild(externalLinksCell);

  return row;
}

function displayViewCounts(track, row, viewCountType) {
  const youtubeStatCell = document.createElement('td');
  youtubeStatCell.className = 'youtube-view-count';

  const spotifyStatCell = document.createElement('td');
  spotifyStatCell.className = 'spotify-view-count';

  const youtubeCurrentViewCount = track.view_count_data_json.Youtube.current_count_json.current_view_count;
  const youtubeInitialViewCount = track.view_count_data_json.Youtube.initial_count_json.initial_view_count;
  const spotifyCurrentViewCount = track.view_count_data_json.Spotify.current_count_json.current_view_count;
  const spotifyInitialViewCount = track.view_count_data_json.Spotify.initial_count_json.initial_view_count;

  switch (viewCountType) {
    case "total-view-count":
      youtubeStatCell.textContent = youtubeCurrentViewCount.toLocaleString();
      spotifyStatCell.textContent = spotifyCurrentViewCount.toLocaleString();
      break;

    case "weekly-view-count":
      const youtubeWeeklyViewCount = youtubeCurrentViewCount - youtubeInitialViewCount;
      const spotifyWeeklyViewCount = spotifyCurrentViewCount - spotifyInitialViewCount;

      youtubeStatCell.textContent = youtubeWeeklyViewCount.toLocaleString();
      spotifyStatCell.textContent = spotifyWeeklyViewCount.toLocaleString();
      break;

    default:
      console.error("Unknown view count type:", viewCountType);
      return;
  }

  row.appendChild(youtubeStatCell);
  row.appendChild(spotifyStatCell);
}

function createSmallPlaylistTableRow(track) {
  const row = document.createElement('tr');

  row.setAttribute('data-isrc', track.isrc);

  const rankCell = document.createElement('td');
  rankCell.className = 'rank';
  rankCell.textContent = track.rank || '';

  const coverCell = document.createElement('td');
  coverCell.className = 'cover';
  const albumCover = document.createElement('img');
  albumCover.className = 'album-cover';
  albumCover.src = track.album_cover_url || '';
  albumCover.alt = 'Album Cover';
  coverCell.appendChild(albumCover);

  const trackInfoCell = document.createElement('td');
  trackInfoCell.className = 'info';
  const trackInfoDiv = document.createElement('div');
  trackInfoDiv.className = 'track-info-div';

  const trackTitle = document.createElement('a');
  trackTitle.className = 'track-title';
  trackTitle.href = track.track_url || '#';
  trackTitle.textContent = track.track_name || 'Unknown Track';

  const artistNameElement = document.createElement('span');
  artistNameElement.className = 'artist-name';
  artistNameElement.textContent = track.artist_name || 'Unknown Artist';

  trackInfoDiv.appendChild(trackTitle);
  trackInfoDiv.appendChild(document.createElement('br'));
  trackInfoDiv.appendChild(artistNameElement);

  trackInfoCell.appendChild(trackInfoDiv);

  const externalLinksCell = document.createElement('td');
  externalLinksCell.className = 'external';
  if (track.youtube_url) {
    const youtubeLink = createSourceLink('YouTube', track.youtube_url);
    externalLinksCell.appendChild(youtubeLink);
  }

  row.appendChild(rankCell);
  row.appendChild(coverCell);
  row.appendChild(trackInfoCell);
  row.appendChild(externalLinksCell);

  return row;
}

function displaySources(cell, track) {
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
  cell.appendChild(sourcesContainer);
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
      return document.createTextNode('');
  }
  linkElement.appendChild(sourceIcon);
  return linkElement;
}

let playlistData = [];

export function sortTable(column, order, viewCountType) {
  const sortedData = playlistData.map(playlist => {
    playlist.tracks.sort((a, b) => {
      let aValue, bValue;

      if (column === 'rank') {
        aValue = a.rank;
        bValue = b.rank;
      } else if (column === 'spotify_views') {
        aValue = getViewCount(a, 'Spotify', viewCountType);
        bValue = getViewCount(b, 'Spotify', viewCountType);
      } else if (column === 'youtube_views') {
        aValue = getViewCount(a, 'Youtube', viewCountType);
        bValue = getViewCount(b, 'Youtube', viewCountType);
      }

      return order === 'asc' ? aValue - bValue : bValue - aValue;
    });
    return playlist;
  });

  displayData(sortedData, 'main-playlist-data-placeholder', true, viewCountType);
}

function getViewCount(track, platform, viewCountType) {
  const currentCount = track.view_count_data_json[platform].current_count_json.current_view_count;
  const initialCount = track.view_count_data_json[platform].initial_count_json.initial_view_count;

  if (viewCountType === "total-view-count") {
    return currentCount;
  } else if (viewCountType === "weekly-view-count") {
    return currentCount - initialCount;
  } else {
    console.error("Unknown view count type:", viewCountType);
    return 0; 
  }
}

export function resetCollapseStates() {
  document.querySelectorAll('.playlist-content').forEach(content => {
    content.classList.remove('collapsed');
  });
  document.querySelectorAll('.collapse-button').forEach(button => {
    button.textContent = '▼';
  });
}

export function addToggleEventListeners() {
  document.querySelectorAll('.collapse-button').forEach(button => {
    button.removeEventListener('click', toggleCollapse);
  });

  document.querySelectorAll('.collapse-button').forEach(button => {
    button.addEventListener('click', toggleCollapse);
  });
}

function toggleCollapse(event) {
  const button = event.currentTarget;
  const targetId = button.getAttribute('data-target');
  const content = document.querySelector(`${targetId} .playlist-content`);
  content.classList.toggle('collapsed');
  button.textContent = content.classList.contains('collapsed') ? '▲' : '▼';
}
