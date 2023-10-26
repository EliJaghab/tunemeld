package main

import (
	"log"

	"github.com/EliJaghab/tunemeld/config"
	"github.com/EliJaghab/tunemeld/extractors"
)

func main() {
	err := config.LoadConfig()
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
		return
	}

	for _, playlistConfig := range config.PlaylistConfigs {
		client := extractors.NewRapidAPIClient()

		bytes, err := client.MakeRequest(playlistConfig)
		if err != nil {
			log.Printf("Error processing %s: %v", playlistConfig.BronzePath, err)
			return
		}
		log.Printf("Successfully processed %s", playlistConfig.BronzePath)

		jsonData, err := extractors.GetJSONfromBytes(bytes)
		if err != nil {
			log.Printf("Error converting to JSON: %v", err)
		}

		err = extractors.WriteJSONToFile(jsonData, playlistConfig.BronzePath)
		if err != nil {
			log.Printf("Error writing %s: %v", playlistConfig.BronzePath, err)
		}
	}
}
