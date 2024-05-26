(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    fetchAndDisplayLastUpdated();
    initializePlaylists('dance');
  });

  function fetchAndDisplayLastUpdated() {
    fetch('./files/last-updated.txt')
      .then((response) => {
        if (!response.ok) {
          throw new Error(
            `Failed to fetch last-updated.txt. Status: ${response.status}`,
          );
        }
        return response.text();
      })
      .then((lastUpdatedDate) => {
        const utcDate = new Date(lastUpdatedDate.trim());
        const etDate = new Date(
          utcDate.toLocaleString('en-US', { timeZone: 'America/New_York' }),
        );
        const formattedDate = etDate.toLocaleString('en-US', {
          month: 'long',
          day: 'numeric',
          year: 'numeric',
          hour: 'numeric',
          minute: '2-digit',
          timeZoneName: 'short',
        });

        const lastUpdatedElement = document.getElementById('last-updated');
        if (lastUpdatedElement) {
          lastUpdatedElement.textContent = `Last Updated - ${formattedDate}`;
        }
      })
      .catch((error) =>
        console.error('Error fetching last updated date:', error),
      );
  }

  function initializePlaylists(genre) {
    const config = {
      dance: {
        Aggregated: './files/aggregated/danceplaylist_gold.json',
        AppleMusic: './files/transform/applemusic_dance_transformed.json',
        SoundCloud: './files/transform/soundcloud_dance_transformed.json',
        Spotify: './files/transform/spotify_dance_transformed.json',
      },
    };

    const playlistConfigs = config[genre];

    if (playlistConfigs) {
      fetchAndDisplayData(
        playlistConfigs.AppleMusic,
        'apple-music-data-placeholder',
      );
      fetchAndDisplayData(
        playlistConfigs.SoundCloud,
        'soundcloud-data-placeholder',
      );
      fetchAndDisplayData(playlistConfigs.Spotify, 'spotify-data-placeholder');
      fetchAndDisplayData(
        playlistConfigs.Aggregated,
        'aggregated-data-placeholder',
        true,
      );
    } else {
      console.error(`No playlist configurations found for genre: ${genre}`);
    }
  }

  function fetchAndDisplayData(filename, placeholderId, isAggregated = false) {
    console.log(`Fetching data from ${filename}...`);

    fetch(filename)
      .then((response) => {
        if (!response.ok) {
          throw new Error(
            `Failed to fetch ${filename}. Status: ${response.status}`,
          );
        }
        return response.json();
      })
      .then((data) => {
        console.log(`Data fetched. Processing...`);
        displayData(data, placeholderId, isAggregated);
      })
      .catch((error) => {
        console.error(`Error fetching and displaying data:`, error);
      });
  }

  function displayData(data, placeholderId, isAggregated = false) {
    const placeholder = document.getElementById(placeholderId);
    if (!placeholder) {
      console.error(`Placeholder with ID ${placeholderId} not found.`);
      return;
    }

    placeholder.innerHTML = '';

    data.forEach((track, _) => {
      const card = createCard(track, isAggregated);
      placeholder.appendChild(card);
    });
  }

  function createCard(track, isAggregated) {
    const card = document.createElement('div');
    card.className = 'card my-1';

    const cardBody = document.createElement('div');
    cardBody.className = 'card-body track-item-content';

    const trackNumber = document.createElement('div');
    trackNumber.className = 'track-number';
    trackNumber.textContent = track.rank;

    const albumCover = document.createElement('img');
    albumCover.className = 'album-cover';
    albumCover.src = track.album_url;
    albumCover.alt = 'Album Cover';

    const trackInfo = document.createElement('div');
    trackInfo.className = 'track-info';

    const trackTitle = document.createElement('a');
    trackTitle.className = 'track-title';
    trackTitle.href = track.link;
    trackTitle.textContent = track.name;

    const artistNameElement = document.createElement('span');
    artistNameElement.className = 'artist-name';
    artistNameElement.textContent = track.artist;

    trackInfo.appendChild(trackTitle);
    trackInfo.appendChild(document.createElement('br'));
    trackInfo.appendChild(artistNameElement);

    cardBody.appendChild(trackNumber);
    cardBody.appendChild(albumCover);
    cardBody.appendChild(trackInfo);

    if (isAggregated) {
      displaySources(cardBody, track);
    }

    card.appendChild(cardBody);
    return card;
  }

  function displaySources(cardBody, track) {
    const sourcesContainer = document.createElement('div');
    sourcesContainer.className = 'track-sources';

    const allSources = {
      ...track.additional_sources,
      [track.source]: track.link,
    };

    Object.keys(allSources).forEach((source) => {
      const sourceLink = allSources[source];
      const linkElement = createSourceLink(source, sourceLink);
      sourcesContainer.appendChild(linkElement);
    });

    cardBody.appendChild(sourcesContainer);
  }

  function createSourceLink(source, sourceLink) {
    const sourceIcon = document.createElement('img');
    const linkElement = document.createElement('a');
    linkElement.href = sourceLink;
    linkElement.target = '_blank';

    sourceIcon.className = 'source-icon';
    switch (source) {
      case 'soundcloud':
        sourceIcon.src = './images/soundcloud_logo.png';
        sourceIcon.alt = 'SoundCloud';
        break;
      case 'spotify':
        sourceIcon.src = './images/spotify_logo.png';
        sourceIcon.alt = 'Spotify';
        break;
      case 'apple_music':
        sourceIcon.src = './images/apple_music_logo.png';
        sourceIcon.alt = 'Apple Music';
        break;
    }

    linkElement.appendChild(sourceIcon);
    return linkElement;
  }
})();