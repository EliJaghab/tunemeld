package main

import (
	"log"

	"github.com/EliJaghab/tunemeld/config"
	"github.com/EliJaghab/tunemeld/extractors"
	"github.com/EliJaghab/tunemeld/gold"
)

func main() {
	err := config.LoadConfig()
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
		return
	}

	var soundCloudTracks, spotifyTracks, appleMusicTracks []config.Track
	soundCloudTracks, err = extractors.ReadTracksFromJSONFile(config.EDMPlaylistConfigs[0].SilverWritePath)
	if err != nil {
		log.Fatalf("Failed to read SoundCloud tracks: %v", err)
		return
	}

	spotifyTracks, err = extractors.ReadTracksFromJSONFile(config.EDMPlaylistConfigs[1].SilverWritePath)
	if err != nil {
		log.Fatalf("Failed to read Spotify tracks: %v", err)
		return
	}

	appleMusicTracks, err = extractors.ReadTracksFromJSONFile(config.EDMPlaylistConfigs[2].SilverWritePath)
	if err != nil {
		log.Fatalf("Failed to read Apple Music tracks: %v", err)
		return
	}

	goldTracks, err := gold.Transform(soundCloudTracks, spotifyTracks, appleMusicTracks)
	if err != nil {
		log.Fatalf("Failed to transform tracks: %v", err)
		return
	}

	var interfaceTracks []config.TrackInterface
	for _, gt := range goldTracks {
		interfaceTracks = append(interfaceTracks, gt)
	}

	goldPath := config.AggregatedPlaylistConfigs["EDMPlaylistConfigs"]
	err = extractors.WriteTracksToJSONFile(interfaceTracks, goldPath)
	if err != nil {
		log.Fatalf("Error writing to gold file %s: %v", goldPath, err)
	}
	log.Printf("Successfully wrote to gold file %s", goldPath)

}
