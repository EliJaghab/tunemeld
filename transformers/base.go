package transformers

import (
	"errors"
	"fmt"
	"log"
	"strings"

	"github.com/EliJaghab/tunemeld/config"
	"github.com/EliJaghab/tunemeld/extractors"
)

type Transformer interface {
    Execute(data []map[string]interface{}) ([]config.Track, error)
}

func Transform(playlistConfig config.PlaylistConfig) ([]config.Track, error) {
	bronzeJson, err := extractors.GetJSONfromFile(playlistConfig.BronzePath)
	if err != nil {
		log.Printf("Error converting to JSON: %v", err)
		return nil, err
	}

	items, err := extractTracks(bronzeJson)
	if err != nil {
		log.Printf("Error extracting tracks: %v", err)
		return nil, err
	}

	transformer, err := getTransformer(playlistConfig.BronzePath)
	if err != nil {
		log.Printf("Error getting transformer: %v", err)
		return nil, err
	}

	tracks, err := transformer.Execute(items) 
	if err != nil {
		log.Printf("Error executing transformer: %v", err)
		return nil, err
	}

	return tracks, nil
}

func extractTracks(bronzeJson map[string]interface{}) ([]map[string]interface{}, error) {
	tracksMap, ok := bronzeJson["tracks"].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("bronzeJson['tracks'] is not a map[string]interface{}")
	}

	items, ok := tracksMap["items"].([]map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("missing 'tracks.items' in JSON or 'tracks.items' is not of type []map[string]interface{}")
	}

	return items, nil
}


func getTransformer(filePath string) (Transformer, error) {
	var transformer Transformer
	switch {
	case strings.Contains(filePath, "soundcloud"):
		transformer = &SoundCloudTransformer{}
	case strings.Contains(filePath, "apple"):
		transformer = &AppleMusicTransformer{}
	case strings.Contains(filePath, "spotify"):
		transformer = &SpotifyTransformer{}
	default:
		return nil, errors.New("unsupported service")
	}
	return transformer, nil
}