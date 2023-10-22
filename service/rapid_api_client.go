package service

import (
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
)

type RapidAPIClient struct {
	apiKey        string
	serviceConfig ServiceConfig
}

func NewRapidAPIClient(serviceConfig ServiceConfig) *RapidAPIClient {
	apiKey := os.Getenv("X_RapidAPI_Key")
	return &RapidAPIClient{apiKey: apiKey, serviceConfig: serviceConfig}
}

func (client *RapidAPIClient) MakeRequest(playlistConfig PlaylistConfig) ([]byte, error) {
	baseURL := playlistConfig.ServiceConfig.BaseURL
	playlistParam := playlistConfig.PlaylistParam
	host := playlistConfig.ServiceConfig.Host
	paramKey := playlistConfig.ServiceConfig.ParamKey // Use the ParamKey from the ServiceConfig

	url := fmt.Sprintf("%s?%s=%s", baseURL, paramKey, playlistParam)
	if playlistConfig.RequestOptions != nil {
		url = fmt.Sprintf("%s&offset=%d&limit=%d", url, playlistConfig.RequestOptions.Offset, playlistConfig.RequestOptions.Limit)
	}
	log.Printf("Preparing request to URL: %s with host: %s", url, host)
	log.Printf("Preparing request to URL: %s with host: %s", url, client.serviceConfig.Host)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		log.Printf("Error creating new request: %v", err)
		return nil, err
	}
	req.Header.Add("X-RapidAPI-Key", client.apiKey)
	req.Header.Add("X-RapidAPI-Host", client.serviceConfig.Host)

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
