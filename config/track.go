package config

type Track struct {
	Name   string `json:"name"`
	Artist string `json:"artist"`
	Link   string `json:"link"`
	Rank   int    `json:"rank"`
}
