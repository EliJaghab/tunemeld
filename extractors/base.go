package extractors

import (
	"errors"
	"fmt"
	"net/http"
	"os"
	"strings"

	"github.com/EliJaghab/tunemeld/config"
)

type RapidAPIClient struct {
	apiKey string
}

func NewRapidAPIClient() *RapidAPIClient {
	apiKey := os.Getenv("X_RapidAPI_Key")
	fmt.Println("apiKey:", apiKey)
	return &RapidAPIClient{apiKey: apiKey}
}

func NewRequest(url string, host string, apiKey string) (*http.Request, error) {
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("error creating request: %w", err)
	}
	req.Header.Add("X-RapidAPI-Key", apiKey)
	req.Header.Add("X-RapidAPI-Host", host)
	return req, nil
}

type Extractor interface {
	GetPlaylist(playlistConfig config.PlaylistConfig) ([]byte, error)
}

func (client *RapidAPIClient) MakeRequest(playlistConfig config.PlaylistConfig) ([]byte, error) {
	var fetcher Extractor
	switch {
	case strings.Contains(playlistConfig.BronzePath, "soundcloud"):
		fetcher = &SoundCloudFetcher{client: client}
	case strings.Contains(playlistConfig.BronzePath, "apple"):
		fetcher = &AppleMusicFetcher{client: client}
	case strings.Contains(playlistConfig.BronzePath, "spotify"):
		fetcher = &SpotifyFetcher{client: client}
	default:
		return nil, errors.New("unsupported service")
	}

	bytesData, err := fetcher.GetPlaylist(playlistConfig)
	if err != nil {
		return nil, fmt.Errorf("error fetching playlist: %w", err)
	}

	return bytesData, nil
}
