// High-Level Functions: Entry points and main logic

export function setupBodyClickListener() {
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

export function setupClosePlayerButton() {
  const closeButton = document.getElementById('close-player-button');
  if (closeButton) {
    closeButton.addEventListener('click', closePlayer);
  } else {
    console.error("Close player button not found.");
  }
}

function handleLinkClick(event, link) {
  const url = link.href;
  const serviceType = getServiceType(url);

  if (serviceType !== 'none') {
    event.preventDefault();
    openPlayer(url, serviceType);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

function openPlayer(url, serviceType) {
  const placeholder = document.getElementById('service-player-placeholder');
  const closeButton = document.getElementById('close-player-button');

  // Clear any previous content
  placeholder.innerHTML = '';

  // Create a new iframe element
  const iframe = document.createElement('iframe');
  iframe.width = '100%';
  iframe.style.border = 'none';

  let showVolumeControl = false;

  // Set iframe properties based on service type
  switch (serviceType) {
    case 'soundcloud':
      iframe.src = `https://w.soundcloud.com/player/?url=${encodeURIComponent(url)}&auto_play=true`;
      iframe.allow = 'autoplay';
      iframe.height = '166';
      showVolumeControl = true;
      break;
    case 'spotify':
      const spotifyId = getSpotifyTrackId(url);
      iframe.src = `https://open.spotify.com/embed/${spotifyId}`;
      iframe.allow = 'encrypted-media';
      iframe.height = '80';
      break;
    case 'applemusic':
      const appleMusicId = getAppleMusicId(url);
      iframe.src = `https://embed.music.apple.com/us/album/${appleMusicId}`;
      iframe.allow = 'autoplay *; encrypted-media *;';
      iframe.height = '450';
      break;
    case 'youtube':
      iframe.src = `https://www.youtube.com/embed/${getYouTubeVideoId(url)}?autoplay=1`;
      iframe.allow = 'autoplay; encrypted-media';
      iframe.referrerPolicy = 'no-referrer-when-downgrade';
      iframe.height = '315';
      break;
    default:
      console.error("Unsupported service type:", serviceType);
  }

  // Load iframe and then volume slider
  iframe.onload = function() {
    toggleVolumeControl(showVolumeControl);
    closeButton.style.display = 'block';
  };

  placeholder.appendChild(iframe);
}

function closePlayer() {
  const placeholder = document.getElementById('service-player-placeholder');
  const closeButton = document.getElementById('close-player-button');

  if (placeholder) placeholder.innerHTML = '';
  if (closeButton) closeButton.style.display = 'none';

  toggleVolumeControl(false);
}

// Low-Level Utility Functions: Supporting functions used by mid-level functions

function getServiceType(url) {
  if (isSoundCloudLink(url)) return 'soundcloud';
  if (isSpotifyLink(url)) return 'spotify';
  if (isAppleMusicLink(url)) return 'applemusic';
  if (isYouTubeLink(url)) return 'youtube';
  return 'none';
}

function isSoundCloudLink(url) {
  return /^https:\/\/soundcloud\.com\/[a-zA-Z0-9-_]+\/[a-zA-Z0-9-_]+/.test(url);
}

function isSpotifyLink(url) {
  return /^https:\/\/open\.spotify\.com\/(track|album|playlist)\/[a-zA-Z0-9]+/.test(url);
}

function isAppleMusicLink(url) {
  return /^https:\/\/music\.apple\.com\//.test(url);
}

function isYouTubeLink(url) {
  return /^https:\/\/(www\.)?youtube\.com\/watch\?v=[a-zA-Z0-9_-]+/.test(url);
}

function getSpotifyTrackId(url) {
  const match = url.match(/\/(track|album|playlist)\/([a-zA-Z0-9]+)/);
  return match ? `${match[1]}/${match[2]}` : '';
}

function getAppleMusicId(url) {
  const match = url.match(/\/album\/[^\/]+\/(\d+)\?i=(\d+)/);
  return match ? `${match[1]}?i=${match[2]}` : '';
}

function getYouTubeVideoId(url) {
  const match = url.match(/v=([a-zA-Z0-9_-]+)/);
  return match ? match[1] : '';
}

export function toggleVolumeControl(show) {
  const volumeControl = document.getElementById('volume-control');
  if (volumeControl) {
    volumeControl.style.display = show ? 'block' : 'none';
  }
}

function setVolume(volume) {
  const iframe = document.querySelector('#service-player-placeholder iframe');
  if (iframe && iframe.src.includes('soundcloud.com')) {
    const widget = SC.Widget(iframe);
    widget.setVolume(volume); 
  } else {
    console.error('SoundCloud iframe not found for volume setting');
  }
}
