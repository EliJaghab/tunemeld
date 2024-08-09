function openPlayer(url, serviceType) {
  const playerContainer = document.getElementById('player-container');
  const placeholder = document.getElementById('service-player-placeholder');
  const volumeControl = document.getElementById('volume-control');
  const closeButton = document.getElementById('close-player-button');

  placeholder.innerHTML = '';

  const iframe = document.createElement('iframe');
  iframe.width = '100%';
  iframe.style.border = 'none';

  if (serviceType === 'soundcloud') {
    iframe.src = `https://w.soundcloud.com/player/?url=${encodeURIComponent(url)}&auto_play=true`;
    iframe.allow = 'autoplay';
    iframe.height = '166';
    volumeControl.style.display = 'block';  // Show volume control for SoundCloud
    displayAndSetVolume();
    setupVolumeControl();
  } else if (serviceType === 'spotify') {
    const spotifyId = getSpotifyTrackId(url);
    iframe.src = `https://open.spotify.com/embed/${spotifyId}`;
    iframe.allow = 'encrypted-media';
    iframe.height = '80';
    volumeControl.style.display = 'none';  // Hide volume control for Spotify
  } else if (serviceType === 'applemusic') {
    const appleMusicId = getAppleMusicId(url);
    iframe.src = `https://embed.music.apple.com/us/album/${appleMusicId}`;
    iframe.allow = 'autoplay *; encrypted-media *;';
    iframe.height = '450';
    volumeControl.style.display = 'none';  // Hide volume control for Apple Music
  } else if (serviceType === 'youtube') {
    iframe.src = `https://www.youtube.com/embed/${getYouTubeVideoId(url)}?autoplay=1`;
    iframe.allow = 'autoplay; encrypted-media';
    iframe.referrerPolicy = 'no-referrer-when-downgrade';  // Add referrer policy
    iframe.height = '315';
    volumeControl.style.display = 'none';
  }

  placeholder.appendChild(iframe);
  closeButton.style.display = 'block';
}


function isAppleMusicLink(url) {
  const appleMusicPattern = /^https:\/\/music\.apple\.com\//;
  return appleMusicPattern.test(url);
}

function isSoundCloudLink(url) {
  const soundCloudPattern = /^https:\/\/soundcloud\.com\/[a-zA-Z0-9-_]+\/[a-zA-Z0-9-_]+/;
  return soundCloudPattern.test(url);
}

function isSpotifyLink(url) {
  const spotifyPattern = /^https:\/\/open\.spotify\.com\/(track|album|playlist)\/[a-zA-Z0-9]+/;
  return spotifyPattern.test(url);
}

function isYouTubeLink(url) {
  const youtubePattern = /^https:\/\/(www\.)?youtube\.com\/watch\?v=[a-zA-Z0-9_-]+/;
  return youtubePattern.test(url);
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


function displayAndSetVolume() {
  const volumeControl = document.getElementById('volume-control');
  const volumeSlider = document.getElementById('volume-slider');

  if (volumeControl) {
    volumeControl.style.display = 'block';
  } else {
    console.error('Volume control not found');
  }

  if (volumeSlider) {
    volumeSlider.value = 60; 
    setVolume(80);
  } else {
    console.error('Volume slider not found');
  }
}

function setupVolumeControl() {
  const volumeSlider = document.getElementById('volume-slider');
  if (volumeSlider) {
    volumeSlider.addEventListener('input', function() {
      setVolume(this.value);
    });
  } else {
    console.error('Volume slider not found for listener setup');
  }
}

function setVolume(volume) {
  const iframe = document.querySelector('#service-player-placeholder iframe');
  if (iframe) {
    const widget = SC.Widget(iframe);
    widget.setVolume(volume); 
  } else {
    console.error('SoundCloud iframe not found for volume setting');
  }
}

function closePlayer() {
  const placeholder = document.getElementById('service-player-placeholder');
  const closeButton = document.getElementById('close-player-button');
  const volumeControl = document.getElementById('volume-control');
  const playerContainer = document.getElementById('player-container');

  if (placeholder) placeholder.innerHTML = '';
  if (closeButton) closeButton.style.display = 'none';
  if (volumeControl) volumeControl.style.display = 'none';
  if (playerContainer) playerContainer.style.display = 'none';
}

document.getElementById('close-player-button').addEventListener('click', closePlayer);

document.addEventListener('DOMContentLoaded', function() {
  const volumeControl = document.getElementById('volume-control');
  volumeControl.style.display = 'none';
});
