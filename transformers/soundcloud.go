package transformers

import (
	"encoding/json"
	"fmt"

	"github.com/EliJaghab/tunemeld/config"
)

type SoundCloudTransformer struct{}

func (t *SoundCloudTransformer) Execute(data []map[string]interface{}) ([]config.Track, error) {

	items, ok := data["tracks"]["items"]
	if !ok {
		return nil, fmt.Errorf("missing 'tracks.items' in JSON")
	}

	var tracks []config.Track
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

		track := config.Track{
			Name:   name,
			Artist: artist,
			Link:   permalink,
			Rank:   i + 1,
		}
		tracks = append(tracks, track)
	}

	return tracks, nil
}
