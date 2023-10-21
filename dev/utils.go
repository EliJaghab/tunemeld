package dev

import (
	"fmt"
	"encoding/json"
	"os"
)


func IsDevelopmentMode() bool {
	return os.Getenv("DEVELOPMENT") == "True"
}

func FetchDevData(serviceName string) (map[string]interface{}, error) {
	if !IsDevelopmentMode() {
		return nil, fmt.Errorf("operation not allowed: not in development mode")
	}

	filePath, err := GetCachedJSONFilePath(serviceName)
	if err != nil {
		return nil, err
	}

	data, err := LoadJSONFromFile(filePath)
	if err != nil {
		return nil, err
	}

	return data, nil
}

func GetCachedJSONFilePath(serviceName string) (string, error) {
	filePath, found := CachedJSONFiles[serviceName]
	if !found {
		return "", fmt.Errorf("Error: no JSON file path found for service: %s\n", serviceName)
	}
	return filePath, nil
}

func LoadJSONFromFile(filename string) (map[string]interface{}, error) {
	data, err := os.ReadFile(filename)
	if err != nil {
		return nil, err
	}

	var result map[string]interface{}
	err = json.Unmarshal(data, &result)
	if err != nil {
		return nil, err
	}

	return result, nil
}
