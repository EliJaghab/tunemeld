package transformers

import (
	"fmt"
	"log"
	"strconv"

	"github.com/EliJaghab/tunemeld/config"
)

type AppleMusicTransformer struct{}

func (t *AppleMusicTransformer) Execute(data []map[string]interface{}) ([]config.Track, error) {
	log.Println("Executing AppleMusicTransformer...")

	if len(data) == 0 {
		return nil, fmt.Errorf("data is empty")
	}

	albumDetailsInterface, ok := data[0]["album_details"]
	if !ok {
		return nil, fmt.Errorf("album details not found in data")
	}

	albumDetails, ok := albumDetailsInterface.(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("invalid album details format")
	}

	var tracks []config.Track
	for rankStr, trackDataInterface := range albumDetails {
		rank, err := strconv.Atoi(rankStr)
		if err != nil {
			log.Printf("Warning: Skipping rank %s due to conversion error: %v", rankStr, err)
			continue
		}

		rank = rank + 1 // Rank is 1-indexed, array is 0-indexed

		trackData, ok := trackDataInterface.(map[string]interface{})
		if !ok {
			return nil, fmt.Errorf("invalid track data format")
		}

		trackName, ok := trackData["name"].(string)
		if !ok {
			return nil, fmt.Errorf("invalid track name format")
		}

		artistName, ok := trackData["artist"].(string)
		if !ok {
			return nil, fmt.Errorf("invalid artist name format")
		}

		albumURL, err := GetAlbumURL(trackName, artistName)
		if err != nil {
			log.Printf("Warning: failed to get album URL for track %s by artist %s: %v", trackName, artistName, err)
		}

		link, ok := trackData["link"].(string)
		if !ok {
			return nil, fmt.Errorf("invalid link format")
		}

		track := config.Track{
			Name:     trackName,
			Artist:   artistName,
			Link:     link,
			Rank:     rank,
			AlbumURL: albumURL,
		}
		tracks = append(tracks, track)
	}

	log.Printf("Successfully transformed %d tracks", len(tracks))
	return tracks, nil
}
