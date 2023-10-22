package service

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
)

type RapidAPIClient struct {
	apiKey        string
	serviceConfig ServiceConfig
}

func NewRapidAPIClient(serviceConfig ServiceConfig) *RapidAPIClient {
	apiKey := os.Getenv("X_RapidAPI_Key")
	return &RapidAPIClient{apiKey: apiKey, serviceConfig: serviceConfig}
}

func NewRequest(url string, client *RapidAPIClient) (*http.Request, error) {
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Add("X-RapidAPI-Key", client.apiKey)
	req.Header.Add("X-RapidAPI-Host", client.serviceConfig.Host)
	return req, nil
}

func FetchPage(url string, client *RapidAPIClient) ([]map[string]interface{}, int, error) {
	req, err := NewRequest(url, client)
	if err != nil {
		fmt.Printf("Error creating new request: %v\n", err)
		return nil, 0, err
	}

	res, err := http.DefaultClient.Do(req)
	if err != nil {
		fmt.Printf("Error making HTTP request: %v\n", err)
		return nil, 0, err
	}
	defer res.Body.Close()

	body, err := io.ReadAll(res.Body)
	if err != nil {
		fmt.Printf("Error reading response body: %v\n", err)
		return nil, 0, err
	}

	var responseMap map[string]interface{}
	err = json.Unmarshal(body, &responseMap)
	if err != nil {
		fmt.Printf("Error unmarshaling response body: %v\n", err)
		return nil, 0, err
	}

	tracks, ok := responseMap["tracks"].(map[string]interface{})
	if !ok {
		fmt.Println("Invalid track data format")
		return nil, 0, errors.New("invalid track data format")
	}

	items, ok := tracks["items"].([]interface{})
	if !ok || len(items) == 0 {
		fmt.Println("No more items")
		return nil, 0, errors.New("no more items")
	}

	allTracks := make([]map[string]interface{}, 0)
	for _, item := range items {
		itemMap, ok := item.(map[string]interface{})
		if ok {
			allTracks = append(allTracks, itemMap)
		}
	}

	nextOffsetValue, ok := tracks["nextOffset"]
	if !ok || nextOffsetValue == nil {
		fmt.Println("No next offset value")
		return allTracks, 0, nil
	}

	nextOffset, ok := nextOffsetValue.(float64)
	if !ok {
		fmt.Printf("Invalid next offset value: %v\n", nextOffsetValue)
		return allTracks, 0, fmt.Errorf("invalid next offset value: %v", nextOffsetValue)
	}

	fmt.Printf("Next offset value: %d\n", int(nextOffset))
	fmt.Printf("Number of tracks fetched in this call: %d\n", len(allTracks))

	return allTracks, int(nextOffset), nil
}

func (client *RapidAPIClient) MakeRequest(playlistConfig PlaylistConfig) ([]byte, error) {
	var allTracks []map[string]interface{}
	offset := 0
	limit := 50

	for {
		url := fmt.Sprintf("%s?%s=%s", playlistConfig.ServiceConfig.BaseURL, playlistConfig.ServiceConfig.ParamKey, playlistConfig.PlaylistParam)
		if strings.Contains(playlistConfig.BronzePath, "soundcloud") {
			url = fmt.Sprintf("%s&offset=%d&limit=%d", url, offset, limit)
		}

		fmt.Printf("Fetching page with URL: %s\n", url)
		tracks, nextOffset, err := FetchPage(url, client)
		if err != nil {
			fmt.Printf("Error fetching page: %v\n", err)
			return nil, err
		}
		allTracks = append(allTracks, tracks...)
		if !strings.Contains(playlistConfig.BronzePath, "soundcloud") || nextOffset == 0 {
			break
		}
		offset = nextOffset
	}

	fmt.Printf("Total number of tracks fetched: %d\n", len(allTracks))

	combinedResponse := map[string]interface{}{
		"tracks": map[string]interface{}{
			"items": allTracks,
		},
	}
	combinedJSON, err := json.Marshal(combinedResponse)
	if err != nil {
		fmt.Printf("Error marshaling combined response: %v\n", err)
		return nil, err
	}

	return combinedJSON, nil
}
