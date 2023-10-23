package transform

import (
	"encoding/json"
	"fmt"
)

func SoundCloud(data []byte) ([]Track, error) {
	var result map[string]map[string][]map[string]interface{}
	err := json.Unmarshal(data, &result)
	if err != nil {
		return nil, fmt.Errorf("error parsing JSON: %w", err)
	}

	items, ok := result["tracks"]["items"]
	if !ok {
		return nil, fmt.Errorf("missing 'tracks.items' in JSON")
	}

	var tracks []Track
	for i, item := range items {
		name, ok := item["title"].(string)
		if !ok {
			return nil, fmt.Errorf("missing or invalid 'title' in item %d", i)
		}

		permalink, ok := item["permalink"].(string)
		if !ok {
			return nil, fmt.Errorf("missing or invalid 'permalink' in item %d", i)
		}

		user, ok := item["user"].(map[string]interface{})
		if !ok {
			return nil, fmt.Errorf("missing or invalid 'user' in item %d", i)
		}

		artist, ok := user["name"].(string)
		if !ok {
			return nil, fmt.Errorf("missing or invalid 'user.name' in item %d", i)
		}

		track := Track{
			Name:   name,
			Artist: artist,
			Link:   permalink,
			Rank:   i + 1,
		}
		tracks = append(tracks, track)
	}

	return tracks, nil
}
