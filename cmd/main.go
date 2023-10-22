package main

import (
	"log"
	"github.com/EliJaghab/tunemeld/service"  // Replace with the actual import path
)

func main() {
	for _, playlistConfig := range service.PlaylistConfigs {
		client := service.NewRapidAPIClient(playlistConfig.ServiceConfig)
		
		err := service.GetAndWritePlaylist(client, playlistConfig)
		if err != nil {
			log.Printf("Error processing %s: %v", playlistConfig.CachedFilePath, err)
			continue 
		}
		log.Printf("Successfully processed %s", playlistConfig.CachedFilePath)
	}
}
