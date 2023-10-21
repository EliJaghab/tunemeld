package service

import (
    "github.com/EliJaghab/go_migration/constants"
    "github.com/EliJaghab/go_migration/rapidapi"
    "os"
)


func local() {
    apiKey := os.Getenv("X_RapidAPI_Key")
    client := rapidapi.NewRapidAPIClient(apiKey)
    
    appleMusicURL := constants.AppleMusicBaseURL + constants.AppleMusicPlaylist
    client.MakeRequest(appleMusicURL, constants.AppleMusicHost)
    
    soundCloudURL := constants.SoundCloudBaseURL + constants.SoundCloudPlaylist
    client.MakeRequest(soundCloudURL, constants.oundCloudHost)
    
    spotifyURL := constants.SpotifyBaseURL + constants.SpotifyPlaylist
    client.MakeRequest(spotifyURL, constants.SpotifyHost)
}
