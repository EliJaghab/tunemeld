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
			"name": "Starting From Scratch",
			"artist": "k?d",
			"link": "https://soundcloud.com/ophelia_records/kd-starting-from-scratch",
			"rank": 1,
			"album_url": "https://i1.sndcdn.com/artworks-iGWgY4yu6vqyFBi4-K0aVuA-original.jpg",
			"source": "soundcloud"
		},
		{
			"name": "Fine Fine Baby",
			"artist": "Jamie Jones Kah-Lo",
			"link": "https://soundcloud.com/jamie-jones/jamie-jones-kah-lo-fine-fine",
			"rank": 15,
			"album_url": "https://i1.sndcdn.com/artworks-NNd59rC0VBnD-0-original.jpg",
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
			"name": "Starting From Scratch",
			"artist": "k?d",
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
			"name": "Starting From Scrat",
			"artist": "k?d",
			"link": "https://soundcloud.com/ophelia_records/kd-starting-from-scratch",
			"rank": 1,
			"album_url": "https://i1.sndcdn.com/artworks-iGWgY4yu6vqyFBi4-K0aVuA-original.jpg",
			"source": "apple_music"
		},
		{
			"name": "Fine Fine Baby",
			"artist": "Jamie Jones Kah-Lo",
			"link": "https://music.apple.com/us/album/fine-fine-baby/1716830861?i=1716830862",
			"rank": 1,
			"album_url": "https://i.scdn.co/image/ab67616d0000b27347a4342599e08e8294356f68",
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
	
	expectedTracks := []config.Track{
		{
			Name:              "Starting From Scratch",
			Artist:            "k?d",
			Link:              "https://soundcloud.com/ophelia_records/kd-starting-from-scratch",
			Rank:              1,
			AlbumURL:          "https://i1.sndcdn.com/artworks-iGWgY4yu6vqyFBi4-K0aVuA-original.jpg",
			Source:            config.SourceSoundCloud,
			AdditionalSources: []config.TrackSource{config.SourceAppleMusic, config.SourceSpotify},
		},
		{
			Name:              "Fine Fine Baby",
			Artist:            "Jamie Jones Kah-Lo",
			Link:              "https://soundcloud.com/jamie-jones/jamie-jones-kah-lo-fine-fine",
			Rank:              2, 
			AlbumURL:          "https://i1.sndcdn.com/artworks-NNd59rC0VBnD-0-original.jpg",
			Source:            config.SourceSoundCloud,
			AdditionalSources: []config.TrackSource{config.SourceAppleMusic},
		},
	}

	expectedJSON, _ := json.MarshalIndent(expectedTracks, "", "  ")
	actualJSON, _ := json.MarshalIndent(transformedTracks, "", "  ")

	if !reflect.DeepEqual(transformedTracks, expectedTracks) {
		t.Errorf("Expected tracks:\n%s\n\nGot tracks:\n%s", expectedJSON, actualJSON)
	}
}
