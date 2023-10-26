document.addEventListener("DOMContentLoaded", function() {
    console.log("Silver data loading script loaded and ready.");

    // Function to fetch and display data for a playlist
    function fetchAndDisplaySilverData(playlistName, placeholderId, filename) {
        console.log(`Fetching silver data for ${playlistName} from ${filename}...`);

        fetch(filename)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Failed to fetch ${filename}. Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log(`Silver data fetched for ${playlistName}. Processing...`);

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
            })
            .catch(error => {
                console.error(`Error fetching and displaying silver data for ${playlistName}:`, error);
            });
    }

    // Fetch the configuration data
    fetch('config.json')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to fetch config.json. Status: ${response.status}`);
            }
            return response.json();
        })
        .then(config => {
            console.log('Config data fetched. Processing...');

            // Iterate through the playlist configs and fetch the silver data for each playlist
            config.PlaylistConfigs.forEach(playlistConfig => {
                const playlistName = playlistConfig.ServiceConfig.Host.split('.')[0]; 
                const placeholderId = playlistName.toLowerCase() + '-data-placeholder'; 
                const filename = playlistConfig.SilverPath;

                fetchAndDisplaySilverData(playlistName, placeholderId, filename);
            });
        })
        .catch(error => {
            console.error('Error fetching and processing config data:', error);
        });
});


