package main

import (
	"log"

	"github.com/EliJaghab/tunemeld/config"
	"github.com/EliJaghab/tunemeld/extractors"
	"github.com/EliJaghab/tunemeld/transformers"
)

func main() {
	err := config.LoadConfig()
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
		return
	}

	for _, playlistConfig := range config.EDMPlaylistConfigs {
		tracks, err := transformers.Transform(playlistConfig)
		if err != nil {
			log.Printf("Error transforming %s: %v", playlistConfig.BronzePath, err)
			return
		}
		log.Printf("Successfully transformed %s", playlistConfig.BronzePath)

		err = extractors.WriteTracksToJSONFile(tracks, playlistConfig.SilverWritePath)
		if err != nil {
			log.Printf("Error writing %s: %v", playlistConfig.SilverWritePath, err)
		}
		log.Printf("Successfully wrote %s", playlistConfig.SilverWritePath)
	}
}
