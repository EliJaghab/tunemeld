package service

import (
	"encoding/json"
	"fmt"
    "os"
)

func parseJSON(data []byte) (map[string]interface{}, error) {
    var result map[string]interface{}
    err := json.Unmarshal(data, &result)
    if err != nil {
        return nil, fmt.Errorf("error parsing JSON: %w", err)
    }
    return result, nil
}
func IsDevelopmentMode() bool {
	return os.Getenv("DEVELOPMENT") == "True"
}

func FetchExistingData(filePath string) (map[string]interface{}, error) {
	if !IsDevelopmentMode() {
		return nil, fmt.Errorf("operation not allowed: not in development mode")
	}

	data, err := LoadJSONFromFile(filePath)
	if err != nil {
		return nil, err
	}

	return data, nil
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
