package transformers

import (
	"encoding/json"
	"reflect"
	"testing"

	"github.com/EliJaghab/tunemeld/config"
	"github.com/EliJaghab/tunemeld/transformers"
)

func TestSoundCloudTransformer_Execute(t *testing.T) {
	testJSON := `[{
		"tracks": {
			"items": [
				{
					"title": "Test Track 1",
					"permalink": "http://soundcloud.com/testtrack1",
					"user": {"name": "Test Artist 1"},
					"artworkUrl": "http://imageurl.com/test1.jpg"
				},
				{
					"title": "Test Track 2",
					"permalink": "http://soundcloud.com/testtrack2",
					"user": {"name": "Test Artist 2"},
					"artworkUrl": "http://imageurl.com/test2.jpg"
				}
			]
		}
	}]`

	var data []map[string]interface{}
	err := json.Unmarshal([]byte(testJSON), &data)
	if err != nil {
		t.Fatalf("Failed to unmarshal test JSON: %v", err)
	}

	transformer := transformers.SoundCloudTransformer{}

	tracks, err := transformer.Execute(data)
	if err != nil {
		t.Fatalf("Transformer execution failed: %v", err)
	}

	expectedTracks := []config.Track{
		{
			Name:     "Test Track 1",
			Artist:   "Test Artist 1",
			Link:     "http://soundcloud.com/testtrack1",
			Rank:     1,
			AlbumURL: "http://imageurl.com/test1.jpg",
			Source:   config.SourceSoundCloud,
		},
		{
			Name:     "Test Track 2",
			Artist:   "Test Artist 2",
			Link:     "http://soundcloud.com/testtrack2",
			Rank:     2,
			AlbumURL: "http://imageurl.com/test2.jpg",
			Source:   config.SourceSoundCloud,
		},
	}


	if !reflect.DeepEqual(tracks, expectedTracks) {
		t.Errorf("Expected tracks %+v, got %+v", expectedTracks, tracks)
	}
}