package transformers

import (
	"errors"
	"log"
	"strings"

	"github.com/EliJaghab/tunemeld/config"
	"github.com/EliJaghab/tunemeld/extractors"
)

type Transformer interface {
	Execute(data []map[string]interface{}) ([]config.Track, error)
}

func Transform(playlistConfig config.PlaylistConfig) ([]config.Track, error) {
	bronzeJSON, err := extractors.GetJSONfromFile(playlistConfig.BronzePath)
	if err != nil {
		log.Printf("Error converting to JSON: %v", err)
		return nil, err
	}

	transformer, err := getTransformer(playlistConfig.BronzePath)
	if err != nil {
		log.Printf("Error getting transformer: %v", err)
		return nil, err
	}

	var data []map[string]interface{}
	data = append(data, bronzeJSON)

	tracks, err := transformer.Execute(data)
	if err != nil {
		log.Printf("Error executing transformer: %v", err)
		return nil, err
	}

	return tracks, nil
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
