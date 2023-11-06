// Module for handling the display of playlist data
const PlaylistDisplay = (() => {
    // Function to create and append card elements for each track
    function createCardElement(track, index) {
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

        const artistNameElement = document.createElement("span"); 
        artistNameElement.className = "artist-name"; 
        artistNameElement.textContent = track.artist;

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

        return card;
    }

    return {
        fetchAndDisplaySilverData,
    };
})();

// Main module for handling page initialization and configuration loading
const Main = (() => {
    function initializePlaylists(config, genre) {
        const playlistConfigsKey = genre + 'PlaylistConfigs';
        const playlistConfigs = config[playlistConfigsKey];
    
        if (playlistConfigs) {
            playlistConfigs.forEach(playlistConfig => {
                const { SilverReadPath, ServiceName } = playlistConfig;  // Get ServiceName from the config
                const silverFilename = SilverReadPath;
                const placeholderId = ServiceName + '-data-placeholder';  // Use ServiceName to generate placeholderId
    
                PlaylistDisplay.fetchAndDisplaySilverData(ServiceName, placeholderId, silverFilename);
            });
        } else {
            console.error(`No playlist configurations found for genre: ${genre}`);
        }
    };
})();

document.addEventListener("DOMContentLoaded", function () {
    const genreSelector = document.createElement('select');
    // ... (same as before, including the genre selector setup and event listener)

    genreSelector.addEventListener('change', function () {
        const selectedGenre = this.value;
        Main.loadConfigurationAndInitialize(selectedGenre);
    });

    // Initial load of EDM playlists
    genreSelector.value = 'EDM';
    genreSelector.dispatchEvent(new Event('change'));
});
