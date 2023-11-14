package gold

import (
	"encoding/json"
	"os"

	"github.com/EliJaghab/tunemeld/config"
)

func GetTracksFromFile(filename string) ([]config.Track, error) {
	data, err := os.ReadFile(filename)
	if err != nil {
		return nil, err
	}

	var tracks []config.Track
	err = json.Unmarshal(data, &tracks)
	if err != nil {
		return nil, err
	}

	return tracks, nil
}
