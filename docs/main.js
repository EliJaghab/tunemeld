(function () {
    'use strict';

    document.addEventListener("DOMContentLoaded", function () {
        console.log("Document loaded and ready.");

        // Function to fetch and display data for a playlist
        function fetchAndDisplayData(playlistName, placeholderId, filename) {
            console.log(`Fetching data for ${playlistName} from ${filename}...`);

            fetch(filename)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Failed to fetch ${filename}. Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log(`Data fetched for ${playlistName}. Processing...`);
        
                    // Sort the data array by rank in ascending order
                    data.sort((a, b) => a.rank - b.rank);
        
                    const placeholder = document.getElementById(placeholderId);
                    if (!placeholder) {
                        console.error(`Placeholder with ID ${placeholderId} not found.`);
                        return;
                    }

                    placeholder.innerHTML = ""; // Clear the placeholder

                    // Iterate through the playlist data and create HTML elements
                    data.forEach((track, index) => {
                        console.log(`Processing track ${index + 1} for ${playlistName}...`);
                    
                        const card = document.createElement("div");
                        card.className = "card my-1";
                    
                        const cardBody = document.createElement("div");
                        cardBody.className = "card-body track-item-content";
                    
                        const albumCover = document.createElement("img");
                        albumCover.className = "album-cover";
                        albumCover.src = "https://example.com/album-cover.jpg"; // Hard-coded album cover URL
                        albumCover.alt = "Album Cover";
                    
                        const trackNumber = document.createElement("div");
                        trackNumber.className = "track-number";
                        trackNumber.textContent = track.rank;
                    
                        const trackInfo = document.createElement("div");
                        trackInfo.className = "track-info";
                    
                        const trackTitle = document.createElement("a");
                        trackTitle.className = "track-title";
                        trackTitle.href = "#";
                        trackTitle.textContent = track.name;
                    
                        const artistLink = document.createElement("a");
                        artistLink.className = "username";
                        artistLink.href = "#";
                        artistLink.textContent = track.artist;
                    
                        trackInfo.appendChild(trackTitle);
                        trackInfo.appendChild(document.createElement("br"));  // Add a line break between title and artist
                        trackInfo.appendChild(artistLink);
                    
                        cardBody.appendChild(albumCover);
                        cardBody.appendChild(trackNumber);
                        cardBody.appendChild(trackInfo);
                    
                        card.appendChild(cardBody);
                        placeholder.appendChild(card);
                    });
                    
                })
                .catch(error => {
                    console.error(`Error fetching and displaying data for ${playlistName}:`, error);
                });
        }

        // Function to initialize playlists based on configuration and selected genre
        function initializePlaylists(config, genre) {
            const playlistConfigsKey = genre + 'PlaylistConfigs';
            const playlistConfigs = config[playlistConfigsKey];
        
            if (playlistConfigs) {
                playlistConfigs.forEach(playlistConfig => {
                    const { SilverReadPath, ServiceName } = playlistConfig;  // Get ServiceName from the config
                    const silverFilename = SilverReadPath;
                    const placeholderId = ServiceName.toLowerCase() + '-data-placeholder';  // Use ServiceName to generate placeholderId
        
                    fetchAndDisplayData(ServiceName, placeholderId, silverFilename);
                });
            } else {
                console.error(`No playlist configurations found for genre: ${genre}`);
            }
        }

        // Selector for choosing the genre
        const genreSelector = document.createElement('select');
        genreSelector.id = 'genre-selector';
        genreSelector.innerHTML = `
            <option value="EDM">EDM</option>
            <!-- Add other genres as options here -->
        `;
        document.body.appendChild(genreSelector);

        // Event listener for genre selector
        genreSelector.addEventListener('change', function () {
            const selectedGenre = this.value;
            // Load configuration and initialize playlists based on selected genre
            fetch('./config.json')  // assuming your JSON file is named config.json
                .then(response => response.json())
                .then(config => {
                    initializePlaylists(config, selectedGenre);
                })
                .catch(error => console.error('Error loading configuration:', error));
        });

        // Initial load of EDM playlists
        genreSelector.value = 'EDM';
        genreSelector.dispatchEvent(new Event('change'));
    });

})();
