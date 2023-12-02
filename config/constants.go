package config

import (
	"encoding/json"
	"os"
)

const (
	PostgresConnectionString = "postgres://eli:your_password@localhost:5432/postgres?sslmode=disable"
)

const (
	TracksConnectionString = "postgres://eli:your_password@localhost:5432/tracks?sslmode=disable"
)
const (
	ConfigFilePath = "./docs/config.json"
)

type ServiceConfig struct {
	ServiceName string
	BaseURL     string
	Host        string
	ParamKey    string
}

type PlaylistConfig struct {
	PlaylistParam   string
	BronzePath      string
	SilverWritePath string
	ServiceConfig
	RequestOptions *RequestOptions
}

type RequestOptions struct {
	Offset int
	Limit  int
}

type Config struct {
	BronzeRootPath     string
	SilverRootPath     string
	BronzeSuffix       string
	SilverSuffix       string
	ServiceConfigs     map[string]ServiceConfig
	EDMPlaylistConfigs []PlaylistConfig
}

var EDMPlaylistConfigs []PlaylistConfig

func LoadConfig() error {
	file, err := os.Open(ConfigFilePath)
	if err != nil {
		return err
	}
	defer file.Close()

	var cfg Config
	decoder := json.NewDecoder(file)
	if err := decoder.Decode(&cfg); err != nil {
		return err
	}

	EDMPlaylistConfigs = cfg.EDMPlaylistConfigs
	return nil
}
