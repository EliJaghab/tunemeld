async function fetchAndDisplayData(url, placeholderId, isAggregated = false, rank = 'rank') {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch ${url}. Status: ${response.status}`);
    }
    const data = await response.json();
    displayData(data, placeholderId, isAggregated, rank);
  } catch (error) {
    console.error('Error fetching and displaying data:', error);
  }
}

function displayData(data, placeholderId, isAggregated = false, rank = 'rank') {
  const placeholder = document.getElementById(placeholderId);
  if (!placeholder) {
    console.error(`Placeholder with ID ${placeholderId} not found.`);
    return;
  }
  placeholder.innerHTML = '';

  data.forEach(playlist => {
    switch (rank) {
      case 'spotify_view_count':
        playlist.tracks.sort((a, b) => a.spotify_total_view_count_rank - b.spotify_total_view_count_rank);
        break;
      case 'spotify_relative_view_count':
        playlist.tracks.sort((a, b) => a.spotify_relative_view_count_rank - b.spotify_relative_view_count_rank);
        break;
      default:
        playlist.tracks.sort((a, b) => a.rank - b.rank);
        break;
    }
  });

  data.forEach((playlist) => {
    playlist.tracks.forEach((track) => {
      const row = isAggregated ? createTableRow(track, isAggregated, rank) : createSmallPlaylistTableRow(track);
      placeholder.appendChild(row);
    });
  });
}

function createTableRow(track, isAggregated, currentRank) {
  const row = document.createElement('tr');
  
  const rankCell = document.createElement('td');
  rankCell.className = 'rank';
  rankCell.textContent = currentRank === 'default' ? track.rank || '' : 
                          currentRank === 'spotify_view_count' ? track.spotify_total_view_count_rank : 
                          track.spotify_relative_view_count_rank;

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

  const statCell = document.createElement('td');
  statCell.className = 'spotify-view-count';
  statCell.textContent = track.view_count_data_json.Spotify.current_count_json.current_view_count.toLocaleString()
  
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
  row.appendChild(statCell);
  row.appendChild(seenOnCell);
  row.appendChild(externalLinksCell);

  return row;
}

function createSmallPlaylistTableRow(track) {
  const row = document.createElement('tr');

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


function showSkeletonLoaders() {
  document.querySelectorAll('.skeleton, .skeleton-text').forEach(el => {
    el.classList.add('loading');
  });
}

function hideSkeletonLoaders() {
  document.querySelectorAll('.skeleton, .skeleton-text').forEach(el => {
    el.classList.remove('loading');
    el.classList.remove('skeleton');
    el.classList.remove('skeleton-text');
  });
}

function resetCollapseStates() {
  document.querySelectorAll('.playlist-content').forEach(content => {
    content.classList.remove('collapsed');
  });
  document.querySelectorAll('.collapse-button').forEach(button => {
    button.textContent = '▼';
  });
}

function addToggleEventListeners() {
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
