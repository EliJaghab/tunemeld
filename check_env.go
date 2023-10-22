package main

import (
	"fmt"
	"log"
	"os"

	"github.com/EliJaghab/tunemeld/service"
)

func main() {
	fmt.Println("Checking environment variables...")
	vars := []string{
		"X_RapidAPI_Key",
		"DEVELOPMENT",
	}

	for _, v := range vars {
		value, exists := os.LookupEnv(v)
		if !exists {
			fmt.Printf("❌ %s is not set\n", v)
		} else {
			fmt.Printf("✅ %s=%s\n", v, value)
		}
	}

	data, err := service.NewRapidAPIClient().FetchPlaylist(service.AppleMusicConfig, service.AppleMusicEDM)
	if err != nil {
		log.Printf("Error fetching playlist: %v", err)
		return
	}
	log.Print(data)

}
