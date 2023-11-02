package transformers

import (
	"fmt"
	"strconv"

	"github.com/EliJaghab/tunemeld/config"
)

type AppleMusicTransformer struct{}

func (t *AppleMusicTransformer) Execute(data []map[string]interface{}) ([]config.Track, error) {
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
		// Check if rankStr is a numeric string before attempting conversion
		if _, err := strconv.Atoi(rankStr); err != nil {
			continue // Skip non-numeric keys
		}

		rank, _ := strconv.Atoi(rankStr) // Conversion is safe now

		rank = rank + 1 // Rank is 1-indexed, array is 0-indexed

		trackData, ok := trackDataInterface.(map[string]interface{})
		if !ok {
			return nil, fmt.Errorf("invalid track data format")
		}

		trackName := trackData["name"].(string)
		artistName := trackData["artist"].(string)
		albumURL, err := GetAlbumURL(trackName, artistName)
		if err != nil {
			return nil, err // Handle error (e.g., log it, return it, or however you prefer)
		}

		track := config.Track{
			Name:     trackName,
			Artist:   artistName,
			Link:     trackData["link"].(string),
			Rank:     rank,
			AlbumURL: albumURL,
		}
		tracks = append(tracks, track)
	}
	return tracks, nil
}
