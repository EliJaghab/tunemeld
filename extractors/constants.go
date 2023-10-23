package extractors

const (
	BronzeRootPath = "data/bronze/"
	SilverRootPath = "data/silver/"
	BronzeSuffix   = "_bronze.json"
	SilverSuffix   = "_silver.json"
)

type ServiceConfig struct {
	BaseURL  string
	Host     string
	ParamKey string
}

var (
	AppleMusicConfig = ServiceConfig{
		BaseURL:  "https://apple-music24.p.rapidapi.com/playlist1/",
		Host:     "apple-music24.p.rapidapi.com",
		ParamKey: "url",
	}
	SoundCloudConfig = ServiceConfig{
		BaseURL:  "https://soundcloud-scraper.p.rapidapi.com/v1/playlist/tracks",
		Host:     "soundcloud-scraper.p.rapidapi.com",
		ParamKey: "playlist",
	}
	SpotifyConfig = ServiceConfig{
		BaseURL:  "https://spotify23.p.rapidapi.com/playlist_tracks/",
		Host:     "spotify23.p.rapidapi.com",
		ParamKey: "id",
	}
)

type PlaylistConfig struct {
	PlaylistParam string
	BronzePath    string
	SilverPath    string
	ServiceConfig
	RequestOptions *RequestOptions
}

type RequestOptions struct {
	Offset int
	Limit  int
}

var (
	AppleMusicEDMConfig = PlaylistConfig{
		PlaylistParam: "https%3A%2F%2Fmusic.apple.com%2Fus%2Fplaylist%2Fdancexl%2Fpl.6bf4415b83ce4f3789614ac4c3675740",
		BronzePath:    BronzeRootPath + "apple_music_edm" + BronzeSuffix,
		SilverPath:    SilverRootPath + "apple_music_edm" + SilverSuffix,
		ServiceConfig: AppleMusicConfig,
	}
	SoundCloudEDMConfig = PlaylistConfig{
		PlaylistParam: "https%3A%2F%2Fsoundcloud.com%2Fsoundcloud-the-peak%2Fsets%2Fon-the-up-new-edm-hits",
		BronzePath:    BronzeRootPath + "soundcloud_edm" + BronzeSuffix,
		SilverPath:    SilverRootPath + "soundcloud_edm" + SilverSuffix,
		ServiceConfig: SoundCloudConfig,
	}
	SpotifyEDMConfig = PlaylistConfig{
		PlaylistParam:  "37i9dQZF1DX4Wsb4d7NKfP",
		BronzePath:     BronzeRootPath + "spotify_edm" + BronzeSuffix,
		SilverPath:     SilverRootPath + "spotify_edm" + SilverSuffix,
		ServiceConfig:  SpotifyConfig,
		RequestOptions: &RequestOptions{Offset: 0, Limit: 100},
	}
)

var (
	PlaylistConfigs = []PlaylistConfig{
		AppleMusicEDMConfig,
		SoundCloudEDMConfig,
		SpotifyEDMConfig,
	}
)
