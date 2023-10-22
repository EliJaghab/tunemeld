package extractors

import (
	"fmt"
	"io"
	"net/http"
)

type SpotifyFetcher struct {
	client *RapidAPIClient
}

func (f *SpotifyFetcher) GetPlaylist(playlistConfig PlaylistConfig) ([]byte, error) {
	url := fmt.Sprintf(
		"%s?%s=%s&offset=%d&limit=%d",
		playlistConfig.ServiceConfig.BaseURL,
		playlistConfig.ServiceConfig.ParamKey,
		playlistConfig.PlaylistParam,
		playlistConfig.RequestOptions.Offset,
		playlistConfig.RequestOptions.Limit,
	)

	req, err := NewRequest(url, playlistConfig.ServiceConfig.Host, f.client.apiKey)
	if err != nil {
		return nil, fmt.Errorf("error creating new request: %w", err)
	}

	res, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("error making HTTP request: %w", err)
	}
	defer res.Body.Close()

	body, err := io.ReadAll(res.Body)
	if err != nil {
		return nil, fmt.Errorf("error reading response body: %w", err)
	}

	return body, nil
}
