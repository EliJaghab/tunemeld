package config

import (
	"encoding/json"
	"errors"
)

type TrackSource int

const (
	SourceAppleMusic TrackSource = iota
	SourceSpotify
	SourceSoundCloud
)

func (ts TrackSource) String() string {
	switch ts {
	case SourceAppleMusic:
		return "apple_music"
	case SourceSpotify:
		return "spotify"
	case SourceSoundCloud:
		return "soundcloud"
	default:
		return "unknown"
	}
}

func (ts TrackSource) MarshalJSON() ([]byte, error) {
	return json.Marshal(ts.String())
}

func (ts *TrackSource) UnmarshalJSON(b []byte) error {
	var source string
	if err := json.Unmarshal(b, &source); err != nil {
		return err
	}

	switch source {
	case "apple_music":
		*ts = SourceAppleMusic
	case "spotify":
		*ts = SourceSpotify
	case "soundcloud":
		*ts = SourceSoundCloud
	default:
		return errors.New("unknown track source")
	}
	return nil
}

type Track struct {
	Name     string      `json:"name"`
	Artist   string      `json:"artist"`
	Link     string      `json:"link"`
	Rank     int         `json:"rank"`
	AlbumURL string      `json:"album_url"`
	Source   TrackSource `json:"source"`
}
