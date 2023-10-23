package transformers

import (
	"fmt"
	"strconv"

	"github.com/EliJaghab/tunemeld/config"
)

type AppleMusicTransformer struct{}

func (t *AppleMusicTransformer) Execute(data []map[string]interface{}) ([]config.Track, error) {
	albumDetails, ok := data["album_details"].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("invalid data format")
	}

	var tracks []config.Track
	for rankStr, trackDataInterface := range albumDetails {
		rank, err := strconv.Atoi(rankStr)
		if err != nil {
			return nil, err
		}

		trackData, ok := trackDataInterface.(map[string]interface{})
		if !ok {
			return nil, fmt.Errorf("invalid track data format")
		}

		track := config.Track{
			Name:   trackData["name"].(string),
			Artist: trackData["artist"].(string),
			Link:   trackData["link"].(string),
			Rank:   rank,
		}
		tracks = append(tracks, track)
	}
	return tracks, nil
}
