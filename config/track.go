package config

import (
	"encoding/json"
)

type TrackSource int

const (
	SourceAppleMusic TrackSource = iota
	SourceSpotify
	SourceSoundCloud
	SourceUnknown
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
	var err error
	*ts, err = ParseTrackSource(source)
	return err
}

func ParseTrackSource(source string) (TrackSource, error) {
	switch source {
	case "apple_music":
		return SourceAppleMusic, nil
	case "spotify":
		return SourceSpotify, nil
	case "soundcloud":
		return SourceSoundCloud, nil
	default:
		return SourceUnknown, nil
	}
}

type TrackInterface interface {
	MarshalJSON() ([]byte, error)
}
type Track struct {
	Name              string        `json:"name"`
	Artist            string        `json:"artist"`
	Link              string        `json:"link"`
	Rank              int           `json:"rank"`
	AlbumURL          string        `json:"album_url"`
	Source            TrackSource   `json:"source"`
	AdditionalSources []TrackSource `json:"additional_sources,omitempty"`
}

func (t Track) MarshalJSON() ([]byte, error) {
	type Alias Track
	return json.Marshal(&struct {
		*Alias
		Source            string   `json:"source"`
		AdditionalSources []string `json:"additional_sources,omitempty"` // Represent sources as strings
	}{
		Alias:             (*Alias)(&t),
		Source:            t.Source.String(),
		AdditionalSources: sourcesToStrings(t.AdditionalSources),
	})
}

func sourcesToStrings(sources []TrackSource) []string {
	var result []string
	for _, source := range sources {
		result = append(result, source.String())
	}
	return result
}

func (t Track) GetTrackName() string {
	return t.Name
}

func (t Track) GetTrackArtist() string {
	return t.Artist
}

func (t Track) GetTrackLink() string {
	return t.Link
}

func (t Track) GetTrackRank() int {
	return t.Rank
}

func (t Track) GetTrackAlbumURL() string {
	return t.AlbumURL
}

func (t Track) GetTrackSource() TrackSource {
	return t.Source
}

type GoldTrack struct {
	Track             Track
	AdditionalSources []TrackSource `json:"additional_sources"`
}
