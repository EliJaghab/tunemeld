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
      const card = createCard(track, isAggregated, rank);
      placeholder.appendChild(card);
    });
  });
}

function createCard(track, isAggregated, currentRank) {
  const card = document.createElement('div');
  card.className = 'card my-1';
  const cardBody = document.createElement('div');
  cardBody.className = 'card-body track-item-content';

  const trackNumber = document.createElement('div');
  trackNumber.className = 'track-number';

  if (currentRank === 'default') {
    trackNumber.textContent = track.rank || '';
  } else if (currentRank === 'spotify_view_count') {
    trackNumber.textContent = track.spotify_total_view_count_rank;
  } else if (currentRank === 'spotify_relative_view_count') {
    trackNumber.textContent = track.spotify_relative_view_count_rank;
  }

  const albumCover = document.createElement('img');
  albumCover.className = 'album-cover';
  albumCover.src = track.album_cover_url || '';
  albumCover.alt = 'Album Cover';

  const trackInfo = document.createElement('div');
  trackInfo.className = 'track-info';
  const trackTitle = document.createElement('a');
  trackTitle.className = 'track-title';
  trackTitle.href = track.track_url || '#';
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
    const youtubeLink = createSourceLink('YouTube', track.youtube_url);
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
