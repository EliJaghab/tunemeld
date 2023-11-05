package transformers

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/url"
	"os"
	"regexp"

	"github.com/zmb3/spotify"
	"golang.org/x/oauth2/clientcredentials"
)

func GetAlbumURL(trackName string, artistName string) (string, error) {
	config := &clientcredentials.Config{
		ClientID:       os.Getenv("spotify_client_id"),
		ClientSecret:   os.Getenv("spotify_client_secret"),
		TokenURL:       spotify.TokenURL,
		Scopes:         []string{},
		EndpointParams: map[string][]string{},
		AuthStyle:      0,
	}

	httpClient := config.Client(context.Background())
	client := spotify.NewClient(httpClient)

	encodedTrackName := url.QueryEscape(strip(trackName))
	encodedArtistName := url.QueryEscape(strip(artistName))

	query := encodedTrackName + "+artist:" + encodedArtistName

	log.Printf("Searching for track: %s, artist: %s, query: %s\n", trackName, artistName, query)
	results, err := client.Search(query, spotify.SearchTypeTrack)
	if err != nil {
		return "", fmt.Errorf("failed to search Spotify: %w", err)
	}

	if len(results.Tracks.Tracks) == 0 {
		// Debugging: Log the entire response body from Spotify
		log.Println("No tracks found. Debugging response from Spotify:")
		responseBody, err := json.MarshalIndent(results, "", "  ")
		if err != nil {
			log.Printf("Failed to marshal response: %v", err)
		} else {
			log.Println(string(responseBody))
		}
		return "", fmt.Errorf("no tracks found")
	}

	albumID := results.Tracks.Tracks[0].Album.ID
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

func strip(s string) string {
	reg, err := regexp.Compile("[^a-zA-Z0-9]+")
	if err != nil {
		log.Fatal(err)
	}
	return reg.ReplaceAllString(s, " ")
}
