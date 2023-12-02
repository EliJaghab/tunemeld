package transformers

import (
	"encoding/json"

	"reflect"
	"testing"

	"github.com/EliJaghab/tunemeld/config"
	"github.com/EliJaghab/tunemeld/gold"
)

func TestTransform(t *testing.T) {

	soundCloudJSON := `[
		{
			"name": "k?d - Starting From Scratch",
			"artist": "Ophelia Records",
			"link": "https://soundcloud.com/ophelia_records/kd-starting-from-scratch",
			"rank": 1,
			"album_url": "https://i1.sndcdn.com/artworks-iGWgY4yu6vqyFBi4-K0aVuA-original.jpg",
			"source": "soundcloud"
		}
	]`

	spotifyJSON := `[
		{
			"name": "I Believe In Love Again",
			"artist": "Peggy Gou, Lenny Kravitz",
			"link": "https://open.spotify.com/track/4fZ9WECee9p7FEWOUP03jD",
			"rank": 1,
			"album_url": "https://i.scdn.co/image/ab67616d0000b273aa54578ae163a7342b6a82c5",
			"source": "spotify"
		},
		{
			"name": "k?d - Starting From Scratch",
			"artist": "Ophelia Records",
			"link": "https://soundcloud.com/ophelia_records/kd-starting-from-scratch",
			"rank": 6,
			"album_url": "https://i1.sndcdn.com/artworks-iGWgY4yu6vqyFBi4-K0aVuA-original.jpg",
			"source": "spotify"
		}
	]`

	appleMusicJSON := `[
		{
			"name": "Easy",
			"artist": "3LAU & XIRA",
			"link": "https://music.apple.com/us/album/easy/1707025272?i=1707025273",
			"rank": 4,
			"album_url": "https://i.scdn.co/image/ab67616d0000b27374d0e59731efd6a4b05a2e24",
			"source": "apple_music"
		},
		{
			"name": "k?d - Starting From Scrat",
			"artist": "Ophelia Records",
			"link": "https://soundcloud.com/ophelia_records/kd-starting-from-scratch",
			"rank": 1,
			"album_url": "https://i1.sndcdn.com/artworks-iGWgY4yu6vqyFBi4-K0aVuA-original.jpg",
			"source": "apple_music"
		}
	]`

	var soundCloudTracks, spotifyTracks, appleMusicTracks []config.Track
	if err := json.Unmarshal([]byte(soundCloudJSON), &soundCloudTracks); err != nil {
		t.Fatalf("Failed to unmarshal SoundCloud JSON: %v", err)
	}
	if err := json.Unmarshal([]byte(spotifyJSON), &spotifyTracks); err != nil {
		t.Fatalf("Failed to unmarshal Spotify JSON: %v", err)
	}
	if err := json.Unmarshal([]byte(appleMusicJSON), &appleMusicTracks); err != nil {
		t.Fatalf("Failed to unmarshal Apple Music JSON: %v", err)
	}

	transformedTracks, err := gold.Transform(soundCloudTracks, spotifyTracks, appleMusicTracks)
	if err != nil {
		t.Fatalf("Failed to transform tracks: %v", err)
	}

	expectedTracks := []config.GoldTrack{
		{
			Track: config.Track{
				Name:     "k?d - Starting From Scratch",
				Artist:   "Ophelia Records",
				Link:     "https://soundcloud.com/ophelia_records/kd-starting-from-scratch",
				Rank:     1,
				AlbumURL: "https://i1.sndcdn.com/artworks-iGWgY4yu6vqyFBi4-K0aVuA-original.jpg",
				Source:   config.SourceSoundCloud,
			},
			AdditionalSources: []config.TrackSource{config.SourceAppleMusic, config.SourceSpotify},
		},
	}

	expectedJSON, _ := json.MarshalIndent(expectedTracks, "", "  ")
	actualJSON, _ := json.MarshalIndent(transformedTracks, "", "  ")

	if !reflect.DeepEqual(transformedTracks, expectedTracks) {
		t.Errorf("Expected tracks:\n%s\n\nGot tracks:\n%s", expectedJSON, actualJSON)
	}
}
