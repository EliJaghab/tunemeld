package rapidapi


import (
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"net/http"
	"os"
)

type RapidAPIClient struct {
	apiKey string
}

type PlaylistInfo struct {
	BaseURL string
	Host    string
	Param   string
}

var (
	AppleMusicInfo = PlaylistInfo{
		BaseURL: AppleMusicBaseURL,
		Host:    AppleMusicHost,
	}
	SoundCloudInfo = PlaylistInfo{
		BaseURL: SoundCloudBaseURL,
		Host:    SoundCloudHost,
	}
	SpotifyInfo = PlaylistInfo{
		BaseURL: SpotifyBaseURL,
		Host:    SpotifyHost,
	}
)

func NewRapidAPIClient() *RapidAPIClient {
	apiKey := os.Getenv("X_RapidAPI_Key")
	return &RapidAPIClient{apiKey: apiKey}
}

func (client *RapidAPIClient) MakeRequest(url string, host string) {
	log.Printf("getting url: %s from %host", url, host)
	req, _ := http.NewRequest("GET", url, nil)
	req.Header.Add("X-RapidAPI-Key", client.apiKey)
	req.Header.Add("X-RapidAPI-Host", host)

	res, _ := http.DefaultClient.Do(req)
	defer res.Body.Close()

	body, _ := io.ReadAll(res.Body)
	fmt.Println(res)
	fmt.Println(string(body))
	return parseJSON(body)
}

func (client *RapidAPIClient) FetchPlaylist(info PlaylistInfo, playlistParam string) (map[string]interface{}, error) {
	if local.IsDevelopmentMode() {
		var data map[string]interface{}
		err := local.LoadJSONFromFile(local.GetJSONFile(info.Host), &data)
		if err != nil {
			return nil, err
		}
		return data, nil
	}

	url := info.BaseURL + playlistParam
	return client.MakeRequest(url, info.Host)
}

func parseJSON(data []byte) (map[string]interface{}, error) {
	var result map[string]interface{}
	err := json.Unmarshal(data, &result)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal JSON: %w", err)
	}
	return result, nil
}

func (client *RapidAPIClient) FetchAppleMusicPlaylist(playlistURL string) error {
	url := AppleMusicBaseURL + playlistURL
	host := AppleMusicHost
	return client.MakeRequest(url, host)
}

func (client *RapidAPIClient) FetchSoundCloudPlaylist(playlistURL string) error {
	url := SoundCloudBaseURL + playlistURL
	host := SoundCloudHost
	return client.MakeRequest(url, host)
}

func (client *RapidAPIClient) FetchSpotifyPlaylist(playlistID string) error {
	url := SpotifyBaseURL + playlistID
	host := SpotifyHost
	return client.MakeRequest(url, host)
}

