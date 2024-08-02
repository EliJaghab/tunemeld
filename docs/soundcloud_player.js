function openPlayer(url) {
    const playerContainer = document.getElementById('player-container');
    const placeholder = document.getElementById('soundcloud-player-placeholder');
    const volumeControl = document.getElementById('volume-control');
    const closeButton = document.getElementById('close-player-button');
  
    placeholder.innerHTML = '';
  
    const iframe = document.createElement('iframe');
    iframe.src = `https://w.soundcloud.com/player/?url=${encodeURIComponent(url)}&auto_play=true`;
    iframe.allow = 'autoplay';
    iframe.width = '300%';
    iframe.height = '166';
  
    placeholder.appendChild(iframe);

    playerContainer.style.display = 'flex';
    volumeControl.style.display = 'block';
    closeButton.style.display = 'block';
  
    displayAndSetVolume();
    setupVolumeControl();
  }
    
  function isSoundCloudLink(url) {
    const soundCloudPattern = /^https:\/\/soundcloud\.com\/[a-zA-Z0-9-_]+\/[a-zA-Z0-9-_]+/;
    return soundCloudPattern.test(url);
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
      volumeSlider.value = 40;
      setVolume(40);
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
    const iframe = document.querySelector('#soundcloud-player-placeholder iframe');
    if (iframe) {
      const widget = SC.Widget(iframe);
      widget.setVolume(volume);
    } else {
      console.error('SoundCloud iframe not found for volume setting');
    }
  }
  
  function closePlayer() {
    const placeholder = document.getElementById('soundcloud-player-placeholder');
    const closeButton = document.getElementById('close-player-button');
    const volumeControl = document.getElementById('volume-control');
    const playerContainer = document.getElementById('player-container');
  
    if (placeholder) placeholder.innerHTML = '';
    if (closeButton) closeButton.style.display = 'none';
    if (volumeControl) volumeControl.style.display = 'none';
    if (playerContainer) playerContainer.style.display = 'none';
  }
