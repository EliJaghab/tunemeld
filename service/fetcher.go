package service

import (
	"fmt"
	"log"
)

func GetAndWritePlaylist(client *RapidAPIClient, config PlaylistConfig) error {
	body, err := client.MakeRequest(config)
	if err != nil {
		return fmt.Errorf("error making request: %w", err)
	}

	jsonData, err := getJSONfromBytes(body)
	if err != nil {
		return fmt.Errorf("error parsing JSON: %w", err)
	}

	err = WriteJSONToFile(jsonData, config.CachedFilePath)
	if err != nil {
		return fmt.Errorf("error writing JSON to file: %w", err)
	}

	log.Printf("Successfully fetched and wrote playlist data to %s", config.CachedFilePath)

	return nil
}