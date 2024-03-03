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
	SilverReadPath  string // Add SilverReadPath field
	ServiceConfig
	RequestOptions *RequestOptions
}
type RequestOptions struct {
	Offset int
	Limit  int
}

type AggregatedPlaylistConfig struct {
	WritePath string // Add WritePath field
	ReadPath  string // Add ReadPath field
}
type Config struct {
	ServiceConfigs            map[string]ServiceConfig
	EDMPlaylistConfigs        []PlaylistConfig
	AggregatedPlaylistConfigs map[string]AggregatedPlaylistConfig
}

var EDMPlaylistConfigs []PlaylistConfig

var AggregatedPlaylistConfigs map[string]AggregatedPlaylistConfig

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
	AggregatedPlaylistConfigs = cfg.AggregatedPlaylistConfigs
	return nil
}
