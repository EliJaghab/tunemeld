package config

import (
	"encoding/json"
	"os"
)

const (
	ConfigFilePath = "./docs/config.json"
)

type ServiceConfig struct {
	BaseURL  string
	Host     string
	ParamKey string
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

var EDMPlaylistConfigs []PlaylistConfig // Global variable to hold the playlist configs

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

	EDMPlaylistConfigs = cfg.EDMPlaylistConfigs // Load the playlist configs into the global variable
	return nil
}
