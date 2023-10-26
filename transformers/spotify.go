package transformers

import (
	"fmt"

	"github.com/EliJaghab/tunemeld/config"
)

type SpotifyTransformer struct{}

func (t *SpotifyTransformer) Execute(data []map[string]interface{}) ([]config.Track, error) {
	itemsInterface, ok := data[0]["items"]
	if !ok {
		return nil, fmt.Errorf("items not found in data")
	}

	items, ok := itemsInterface.([]interface{})
	if !ok {
		return nil, fmt.Errorf("invalid items format")
	}

	var tracks []config.Track
	for rank, itemInterface := range items {
		item, ok := itemInterface.(map[string]interface{})
		if !ok {
			return nil, fmt.Errorf("invalid item format")
		}

		if item["track"] == nil {
			fmt.Printf("Missing 'track' key in item at index %d\n", rank)
			continue
		}

		trackMap, ok := item["track"].(map[string]interface{})
		if !ok {
			return nil, fmt.Errorf("invalid track data format")
		}

		var artistNames []string
		artistsInterface, ok := trackMap["artists"].([]interface{})
		if ok {
			for _, artistInterface := range artistsInterface {
				artist, ok := artistInterface.(map[string]interface{})
				if ok {
					artistNames = append(artistNames, artist["name"].(string))
				}
			}
		}

		track := config.Track{
			Name:   trackMap["name"].(string),
			Artist: joinArtists(artistNames),
			Link:   trackMap["external_urls"].(map[string]interface{})["spotify"].(string),
			Rank:   rank + 1, // Rank is 1-indexed, array is 0-indexed
		}
		tracks = append(tracks, track)
	}
	return tracks, nil
}

func joinArtists(artists []string) string {
	// This function joins artist names into a single string.
	// Modify this function to format the artist names as you desire.
	return fmt.Sprint(artists)
}
