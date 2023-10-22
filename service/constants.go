package service

const (
    
    AppleMusicEDM = "https%3A%2F%2Fmusic.apple.com%2Fus%2Fplaylist%2Fdancexl%2Fpl.6bf4415b83ce4f3789614ac4c3675740"
    SoundCloudEDM = "https%3A%2F%2Fsoundcloud.com%2Fsoundcloud-the-peak%2Fsets%2Fon-the-up-new-edm-hits"
    SpotifyEDM = "37i9dQZF1DX4Wsb4d7NKfP"
)

type ServiceConfig struct {
	BaseURL string
	Host    string
	CachedFilePath string
}

var (
	AppleMusicConfig = ServiceConfig{
		BaseURL: "https://apple-music24.p.rapidapi.com/playlist1/?url=",
		Host:    "apple-music24.p.rapidapi.com",
		CachedFilePath: "playlist_data/apple_music_cache.json",
	}
	SoundCloudConfig = ServiceConfig{
		BaseURL: "https://soundcloud-scraper.p.rapidapi.com/v1/playlist/metadata?playlist=",
		Host:    "soundcloud-scraper.p.rapidapi.com",
		CachedFilePath: "playlist_data/soundcloud_music_cache.json",
	}
	SpotifyConfig = ServiceConfig{
		BaseURL: "https://spotify23.p.rapidapi.com/playlist/?id=",
		Host:    "spotify23.p.rapidapi.com",
		CachedFilePath: "playlist_data/spotify_music_cache.json",
	}
)