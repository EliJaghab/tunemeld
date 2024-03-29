package transformers

import (
	"fmt"
	"strings"

	"github.com/EliJaghab/tunemeld/config"
)

type SoundCloudTransformer struct{}

func (t *SoundCloudTransformer) Execute(data []map[string]interface{}) ([]config.Track, error) {

	items, ok := data[0]["tracks"].(map[string]interface{})["items"]
	if !ok {
		return nil, fmt.Errorf("missing 'tracks.items' in JSON")
	}

	var tracks []config.Track
	itemsSlice, ok := items.([]interface{})
	if !ok {
		return nil, fmt.Errorf("invalid 'tracks.items' in JSON")
	}

	for i, item := range itemsSlice {
		itemMap, ok := item.(map[string]interface{})
		if !ok {
			return nil, fmt.Errorf("invalid item %d", i)
		}

		originalTitle, ok := itemMap["title"].(string)
		if !ok {
			return nil, fmt.Errorf("missing or invalid 'title' in item %d", i)
		}

		permalink, ok := itemMap["permalink"].(string)
		if !ok {
			return nil, fmt.Errorf("missing or invalid 'permalink' in item %d", i)
		}

		user, ok := itemMap["user"].(map[string]interface{})
		if !ok {
			return nil, fmt.Errorf("missing or invalid 'user' in item %d", i)
		}

		originalArtist, ok := user["name"].(string)
		if !ok {
			return nil, fmt.Errorf("missing or invalid 'user.name' in item %d", i)
		}

		albumURL, ok := itemMap["artworkUrl"].(string)
		if !ok {
			return nil, fmt.Errorf("missing or invalid 'artworkUrl' in item %d", i)
		}

		// Handle titles with hyphens
		name := originalTitle
		artist := originalArtist
		if hyphenIndex := strings.Index(originalTitle, " - "); hyphenIndex != -1 {
			// Split at the first hyphen
			parts := strings.SplitN(originalTitle, " - ", 2)
			artist = parts[0]
			name = parts[1]
		}

		track := config.Track{
			Name:     name,
			Artist:   artist,
			Link:     permalink,
			Rank:     i + 1,
			AlbumURL: albumURL,
			Source:   config.SourceSoundCloud,
		}

		tracks = append(tracks, track)
	}

	return tracks, nil
}
