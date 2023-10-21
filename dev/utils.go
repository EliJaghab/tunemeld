package dev

import (
	"encoding/json"
	"os"
)


func IsDevelopmentMode() bool {
	return os.Getenv("DEVELOPMENT") == "True"
}

func LoadJSONFromFile(filename string, v interface{}) error {
	data, err := os.ReadFile(filename)
	if err != nil {
		return err
	}
	return json.Unmarshal(data, v)
}
