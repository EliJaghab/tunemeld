document.addEventListener("DOMContentLoaded", function() {
    // Function to fetch and display data for a playlist
    function fetchAndDisplayData(playlistName, placeholderId, filename) {
      fetch(filename)
        .then(response => response.json())
        .then(data => {
          const placeholder = document.getElementById(placeholderId);
          placeholder.innerHTML = ""; // Clear the placeholder
  
          // Iterate through the playlist data and create HTML elements
          data.forEach(track => {
            const card = document.createElement("div");
            card.className = "card my-1";
  
            const cardBody = document.createElement("div");
            cardBody.className = "card-body track-item-content";
  
            const albumCover = document.createElement("img");
            albumCover.className = "album-cover";
            albumCover.src = track.album_cover_url;
            albumCover.alt = "Album Cover";
  
            const trackNumber = document.createElement("div");
            trackNumber.className = "track-number";
            trackNumber.textContent = track.track_number;
  
            const artistLink = document.createElement("a");
            artistLink.className = "username";
            artistLink.href = "#";
            artistLink.textContent = track.artist_name;
  
            const separator1 = document.createElement("span");
            separator1.className = "separator";
            separator1.textContent = "-";
  
            const trackTitle = document.createElement("a");
            trackTitle.className = "track-title";
            trackTitle.href = "#";
            trackTitle.textContent = track.song_title;
  
            cardBody.appendChild(albumCover);
            cardBody.appendChild(trackNumber);
            cardBody.appendChild(artistLink);
            cardBody.appendChild(separator1);
            cardBody.appendChild(trackTitle);
  
            card.appendChild(cardBody);
            placeholder.appendChild(card);
          });
        });
    }
  
    // Fetch and display data for each playlist
    fetchAndDisplayData("SoundCloud", "soundcloud-data-placeholder", "soundcloud_data.json");
    fetchAndDisplayData("Apple Music", "apple-music-data-placeholder", "apple_music_data.json");
    fetchAndDisplayData("Spotify", "spotify-data-placeholder", "spotify_data.json");
    fetchAndDisplayData("Aggregated Playlist", "aggregated-data-placeholder", "aggregated_data.json");
  });
  