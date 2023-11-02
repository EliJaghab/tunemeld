package transformers

import (
	"context"
	"os"

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

	query := trackName + " artist:" + artistName
	results, err := client.Search(query, spotify.SearchTypeTrack)
	if err != nil {
		return "", err
	}

	if len(results.Tracks.Tracks) == 0 {
		return "", nil // Or return an error if no matching track is found
	}

	albumID := results.Tracks.Tracks[0].Album.ID
	album, err := client.GetAlbum(albumID)
	if err != nil {
		return "", err
	}

	albumCoverURL := album.Images[0].URL
	return albumCoverURL, nil
}
