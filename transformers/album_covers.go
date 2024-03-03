package transformers

import (
    "context"
    "encoding/json"
    "fmt"
    "log"
    "net/url"
    "os"
    "regexp"
    "strings"

    "github.com/zmb3/spotify"
    "golang.org/x/oauth2/clientcredentials"
)

func GetAlbumURL(trackName string, artistName string) (string, error) {
    config := &clientcredentials.Config{
        ClientID:     os.Getenv("spotify_client_id"),
        ClientSecret: os.Getenv("spotify_client_secret"),
        TokenURL:     spotify.TokenURL,
    }

    httpClient := config.Client(context.Background())
    client := spotify.NewClient(httpClient)

    encodedTrackName := url.QueryEscape(trackName) // Keep the original track name
    encodedArtistName := url.QueryEscape(artistName) // Keep the original artist name

    query := fmt.Sprintf("track:%s artist:%s", encodedTrackName, encodedArtistName)

    log.Printf("Searching for track: %s, artist: %s, query: %s\n", trackName, artistName, query)
    results, err := client.Search(query, spotify.SearchTypeTrack)
    if err != nil {
        return "", fmt.Errorf("failed to search Spotify: %w", err)
    }

    if len(results.Tracks.Tracks) == 0 {
        return "", fmt.Errorf("no tracks found")
    }

    for _, track := range results.Tracks.Tracks {
        // Simplified artist name check (consider more complex matching if necessary)
        for _, artist := range track.Artists {
            if strings.EqualFold(artist.Name, artistName) {
                albumID := track.Album.ID
                album, err := client.GetAlbum(albumID)
                if err != nil {
                    return "", fmt.Errorf("failed to get album from Spotify: %w", err)
                }

                if len(album.Images) == 0 {
                    return "", fmt.Errorf("no images available for album")
                }

                albumCoverURL := album.Images[0].URL
                return albumCoverURL, nil
            }
        }
    }

    return "", fmt.Errorf("no matching tracks found")
}

func strip(s string) string {
    // Allow spaces and certain special characters by not stripping them
    reg, err := regexp.Compile("[^a-zA-Z0-9\\s-]+")
    if err != nil {
        log.Fatal(err)
    }
    return reg.ReplaceAllString(s, " ")
}