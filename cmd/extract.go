package main

import (
	"log"
	"github.com/EliJaghab/tunemeld/extractors"
)

func main() {
	for _, playlistConfig := range extractors.PlaylistConfigs {
		client := extractors.NewRapidAPIClient()

		bytes, err := client.MakeRequest(playlistConfig)
		if err != nil {
			log.Printf("Error processing %s: %v", playlistConfig.BronzePath, err)
			log.Printf("Error making request: %v", err)
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