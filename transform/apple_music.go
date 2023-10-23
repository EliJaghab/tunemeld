package transform

import (
	"fmt"
	"strconv"
)

func AppleMusic(data map[string]interface{}) ([]Track, error) {
	albumDetails, ok := data["album_details"].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("invalid data format")
	}

	var tracks []Track
	for rankStr, trackDataInterface := range albumDetails {
		rank, err := strconv.Atoi(rankStr)
		if err != nil {
			return nil, err
		}

		trackData, ok := trackDataInterface.(map[string]interface{})
		if !ok {
			return nil, fmt.Errorf("invalid track data format")
		}

		track := Track{
			Name:   trackData["name"].(string),
			Artist: trackData["artist"].(string),
			Link:   trackData["link"].(string),
			Rank:   rank,
		}
		tracks = append(tracks, track)
	}
	return tracks, nil
}
