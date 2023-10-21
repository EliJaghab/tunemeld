// local/development.go
package local

import (
	"encoding/json"
	"os"
)

var (
	AppleMusicJSONFile = "dev/dev/apple_music_cache.json"
	SoundCloudJSONFile = "dev/dev/soundcloud_cache.json"
	SpotifyJSONFile    = "dev/dev/spotify_cache.json"
)

func IsDevelopmentMode() bool {
	return os.Getenv("DEVELOPMENT") == "True"
}

func LoadJSONFromFile(filename string, v interface{}) error {
	data, err := os.ReadFile(filename)
	if err != nil {
		return err
	}
	return json.Unmarshal(data, v)
}
