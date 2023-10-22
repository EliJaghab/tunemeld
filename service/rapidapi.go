package service

import (
	"io"
	"log"
	"net/http"
	"os"
)

type RapidAPIClient struct {
	apiKey string
}

func NewRapidAPIClient() *RapidAPIClient {
	apiKey := os.Getenv("X_RapidAPI_Key")
	return &RapidAPIClient{apiKey: apiKey}
}

func (client *RapidAPIClient) MakeRequest(url string, host string) (map[string]interface{}, error) {
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

	json, err := parseJSON(body)
	if err != nil {
		log.Printf("Error converting to json: %v", err)
	}

	return json, nil
}

func (client *RapidAPIClient) FetchPlaylist(config ServiceConfig, playlistParam string) (map[string]interface{}, error) {
	if IsDevelopmentMode() {
		data, err := FetchExistingData(config.CachedFilePath)
		if err != nil {
			return nil, err
		}
		return data, nil
	}

	url := config.BaseURL + playlistParam
	return client.MakeRequest(url, config.Host)
}
