package service

type ServiceConfig struct {
	BaseURL string
	Host    string
}

var (
	AppleMusicConfig = ServiceConfig{
		BaseURL: AppleMusicBaseURL,
		Host:    AppleMusicHost,
	}
	SoundCloudConfig = ServiceConfig{
		BaseURL: SoundCloudBaseURL,
		Host:    SoundCloudHost,
	}
	SpotifyConfig = ServiceConfig{
		BaseURL: SpotifyBaseURL,
		Host:    SpotifyHost,
	}
)