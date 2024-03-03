package gold

import (
	"fmt"
	"log"
	"sort"
	"strings"

	"github.com/EliJaghab/tunemeld/config"
	"github.com/lithammer/fuzzysearch/fuzzy"
)

// Pseudocode implementation:
// 1. Compare SC and SP tracks, add matches to foundTracks with both sources.
// 2. Compare SC and AP tracks, update foundTracks or add new entries with AP as the source.
// 3. For SP tracks not already processed, compare with AP and update foundTracks or add new entries.

func Transform(soundCloudTracks, spotifyTracks, appleMusicTracks []config.Track) ([]config.Track, error) {
	foundTracks := []config.Track{}
	trackIndex := make(map[string]int) // Map normalized track identifier to index in foundTracks

	// Step 1: Compare SC and SP, and populate foundTracks
	compareAndPopulate(
		&foundTracks,
		soundCloudTracks, spotifyTracks,
		config.SourceSoundCloud, config.SourceSpotify,
		trackIndex,
	)
	// Step 2: Compare SC and AP, update foundTracks accordingly
	compareAndPopulate(
		&foundTracks,
		soundCloudTracks, appleMusicTracks,
		config.SourceSoundCloud, config.SourceAppleMusic,
		trackIndex,
	)
	// Step 3: For SP tracks not already processed, compare with AP and update foundTracks or add new entries
	compareAndPopulate(
		&foundTracks,
		spotifyTracks, appleMusicTracks,
		config.SourceSpotify, config.SourceAppleMusic,
		trackIndex,
	)
	// Sort the additional sources within each track for deterministic order
	SortAdditionalSources(foundTracks)

	// Sort the entire list of tracks by rank and re-rank them starting from 1
	SortAndReRankTracks(foundTracks)

	return foundTracks, nil
}

func compareAndPopulate(
	foundTracks *[]config.Track,
	tracksA, tracksB []config.Track,
	sourceA, sourceB config.TrackSource,
	trackIndex map[string]int,
) {
	for _, trackA := range tracksA {
		for _, trackB := range tracksB {
			if fuzzyMatch(trackA, trackB) {
				identifier := normalizeIdentifier(trackA.Name, trackA.Artist)
				log.Printf("Fuzzy match found: %s by %s", trackA.Name, trackA.Artist)
				if index, exists := trackIndex[identifier]; exists {
					// Update existing entry with additional source
					if !sourceIncluded((*foundTracks)[index].AdditionalSources, sourceB) {
						(*foundTracks)[index].AdditionalSources = append((*foundTracks)[index].AdditionalSources, sourceB)
						log.Printf("Added %s as an additional source for %s by %s", sourceB.String(), trackA.Name, trackA.Artist)
					}
					// Condition to prioritize the ranking
					if exists {
						// Prioritize SoundCloud ranking, then Apple Music, then Spotify
						currentSource := (*foundTracks)[index].Source
						if currentSource == config.SourceSpotify &&
							(sourceA == config.SourceSoundCloud || sourceA == config.SourceAppleMusic) ||
							currentSource == config.SourceAppleMusic && sourceA == config.SourceSoundCloud {
							(*foundTracks)[index].Rank = trackA.Rank // Prioritize rank based on the source order
						}
						// Existing code for updating additional sources...
					}
				} else {
					// Add new entry to foundTracks
					trackA.Source = sourceA
					trackA.AdditionalSources = []config.TrackSource{sourceB}
					*foundTracks = append(*foundTracks, trackA)
					trackIndex[identifier] = len(*foundTracks) - 1
					log.Printf(
						"New track added: %s by %s with sources %s and %s",
						trackA.Name, trackA.Artist,
						sourceA.String(), sourceB.String(),
					)
				}
			}
		}
	}
}

func fuzzyMatch(trackA, trackB config.Track) bool {
	nameDistance := fuzzy.LevenshteinDistance(trackA.Name, trackB.Name)
	artistDistance := fuzzy.LevenshteinDistance(trackA.Artist, trackB.Artist)
	isMatch := nameDistance <= 2 && artistDistance <= 2
	if isMatch {
		log.Printf(
			"Fuzzy matching \"%s\" by \"%s\" with \"%s\" by \"%s\": Match",
			trackA.Name, trackA.Artist, trackB.Name, trackB.Artist,
		)
	}
	return isMatch
}

func normalizeIdentifier(name, artist string) string {
	// Normalize track identifier (e.g., lowercase, remove non-alphanumeric characters)
	// For simplicity, this example only lowercases the strings
	return fmt.Sprintf("%s-%s", strings.ToLower(name), strings.ToLower(artist))
}

func sourceIncluded(sources []config.TrackSource, source config.TrackSource) bool {
	for _, s := range sources {
		if s == source {
			return true
		}
	}
	return false
}

// SortAdditionalSources sorts the additional sources within each track in ascending order.
func SortAdditionalSources(foundTracks []config.Track) {
	for i := range foundTracks {
		sort.Slice(foundTracks[i].AdditionalSources, func(a, b int) bool {
			// sorted by the integer value of the TrackSource
			return foundTracks[i].AdditionalSources[a] < foundTracks[i].AdditionalSources[b]
		})
	}
}

// SortAndReRankTracks sorts the tracks by their original rank and then re-ranks them starting from 1.
func SortAndReRankTracks(foundTracks []config.Track) {
	// Sort foundTracks by their original Rank to ensure they're in ascending order
	sort.Slice(foundTracks, func(i, j int) bool {
		return foundTracks[i].Rank < foundTracks[j].Rank
	})

	// Re-rank tracks sequentially starting from 1
	for i := range foundTracks {
		foundTracks[i].Rank = i + 1
	}
}
