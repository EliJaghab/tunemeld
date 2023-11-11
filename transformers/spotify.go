package transformers

import (
	"fmt"
	"strings"
	
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

		imagesInterface, ok := trackMap["album"].(map[string]interface{})["images"].([]interface{})
		if !ok {
			return nil, fmt.Errorf("invalid images format")
		}

		if len(imagesInterface) == 0 {
			return nil, fmt.Errorf("no images available")
		}

		firstImage, ok := imagesInterface[0].(map[string]interface{})
		if !ok {
			return nil, fmt.Errorf("invalid image format")
		}

		albumCoverURL, ok := firstImage["url"].(string)
		if !ok {
			return nil, fmt.Errorf("invalid url format")
		}

		track := config.Track{
			Name:     trackMap["name"].(string),
			Artist:   joinArtists(artistNames),
			Link:     trackMap["external_urls"].(map[string]interface{})["spotify"].(string),
			AlbumURL: albumCoverURL,
			Rank:     rank + 1,
		}

		tracks = append(tracks, track)
	}
	return tracks, nil
}

func joinArtists(artists []string) string {
	return strings.Join(artists, ", ")

}
