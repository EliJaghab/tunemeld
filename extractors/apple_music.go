package extractors

import (
	"fmt"
	"io"
	"net/http"

	"github.com/EliJaghab/tunemeld/config"
)

type AppleMusicFetcher struct {
	client *RapidAPIClient
}

func (f *AppleMusicFetcher) GetPlaylist(playlistConfig config.PlaylistConfig) ([]byte, error) {
	url := fmt.Sprintf(
		"%s?%s=%s",
		playlistConfig.ServiceConfig.BaseURL,
		playlistConfig.ServiceConfig.ParamKey,
		playlistConfig.PlaylistParam,
	)
	req, err := NewRequest(url, playlistConfig.ServiceConfig.Host, f.client.apiKey) // Use NewRequest function
	if err != nil {
		return nil, err
	}

	res, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()

	body, err := io.ReadAll(res.Body)
	if err != nil {
		return nil, err
	}

	return body, nil
}
