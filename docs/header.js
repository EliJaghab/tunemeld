async function fetchAndDisplayLastUpdated(genre) {
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
  
  async function fetchAndDisplayHeaderArt(genre) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/header-art?genre=${genre}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch header art. Status: ${response.status}`);
      }
      const data = await response.json();
      displayHeaderArt(data);
    } catch (error) {
      console.error('Error fetching header art:', error);
    }
  }
  
  function displayHeaderArt(data) {
    const services = ['SoundCloud', 'AppleMusic', 'Spotify'];
    services.forEach(service => {
      const imagePlaceholder = document.getElementById(`${service.toLowerCase()}-image-placeholder`);
      const descriptionElement = document.getElementById(`${service.toLowerCase()}-description`);
      const titleElement = document.getElementById(`${service.toLowerCase()}-playlist-title`);
      const coverLinkElement = document.getElementById(`${service.toLowerCase()}-cover-link`);
      
      console.log(`Checking elements for ${service}:`);
      console.log('imagePlaceholder:', imagePlaceholder);
      console.log('descriptionElement:', descriptionElement);
      console.log('titleElement:', titleElement);
      console.log('coverLinkElement:', coverLinkElement);
  
      if (data[service]) {
        const playlistCoverUrl = data[service].playlist_cover_url;
        const playlistUrl = data[service].playlist_url;
  
        if (service === 'AppleMusic' && playlistCoverUrl.endsWith('.m3u8')) {
          console.log('Apple Music video URL:', playlistCoverUrl);
          displayAppleMusicVideo(playlistCoverUrl);
        } else {
          if (imagePlaceholder) imagePlaceholder.style.backgroundImage = `url('${playlistCoverUrl}')`;
        }
  
        if (descriptionElement) descriptionElement.textContent = data[service].playlist_cover_description_text;
  
        if (titleElement) {
          titleElement.textContent = data[service].playlist_name;
          titleElement.href = playlistUrl;
        }
  
        if (coverLinkElement) coverLinkElement.href = playlistUrl;
      }
    });
  
    document.querySelectorAll('.description').forEach(element => {
      element.addEventListener('click', function () {
        this.classList.toggle('expanded');
      });
    });
  }
  
    document.querySelectorAll('.description').forEach(element => {
      element.addEventListener('click', function () {
        this.classList.toggle('expanded');
      });
    });
  
  function displayAppleMusicVideo(url) {
    const videoContainer = document.getElementById('applemusic-video-container');
    videoContainer.innerHTML = `
        <video id="applemusic-video" class="video-js vjs-default-skin" muted autoplay loop playsinline controlsList="nodownload nofullscreen noremoteplayback"></video>
    `;
    const video = document.getElementById('applemusic-video');
  
    if (Hls.isSupported()) {
      const hls = new Hls();
      hls.loadSource(url);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, function () {
        video.play();
      });
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = url;
      video.addEventListener('canplay', function () {
        video.play();
      });
    }
  }
  