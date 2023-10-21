package service

import (
	"io"
	"net/http"
	"os"
	"log"
	"github.com/EliJaghab/tunemeld/dev"
)

type RapidAPIClient struct {
	apiKey string
}


func NewRapidAPIClient() *RapidAPIClient {
	apiKey := os.Getenv("X_RapidAPI_Key")
	return &RapidAPIClient{apiKey: apiKey}
}

func (client *RapidAPIClient) MakeRequest(url string, host string) ([]byte, error) {
	log.Printf("Preparing request to URL: %s with host: %s", url, host)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		log.Printf("Error creating new request: %v", err)
		return nil, err
	}
	req.Header.Add("X-RapidAPI-Key", client.apiKey)
	req.Header.Add("X-RapidAPI-Host", host)

	res, err := http.DefaultClient.Do(req)
	if err != nil {
		log.Printf("Error making request: %v", err)
		return nil, err
	}
	defer res.Body.Close()

	log.Printf("Received response status: %s", res.Status)

	body, err := io.ReadAll(res.Body)
	if err != nil {
		log.Printf("Error reading body: %v", err)
		return nil, err
	}

	return body, nil
}

func (client *RapidAPIClient) FetchPlaylist(config ServiceConfig, playlistParam string) (map[string]interface{}, error) {
	if dev.IsDevelopmentMode() {
		data, err := dev.LoadJSONFromFile(dev.AppleMusicJSONFile)
		if err != nil {
			return nil, err
		}
		return data, nil
	}

	url := info.BaseURL + playlistParam
	return client.MakeRequest(url, info.Host)
}




