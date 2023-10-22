package extractors

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
)

func GetJSONfromBytes(data []byte) (map[string]interface{}, error) {
    var result map[string]interface{}
    err := json.Unmarshal(data, &result)
    if err != nil {
        return nil, fmt.Errorf("error parsing JSON: %w, data: %s", err, string(data))
    }
    return result, nil
}

func GetJSONfromFile(filename string) (map[string]interface{}, error) {
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

func WriteJSONToFile(data map[string]interface{}, filePath string) error {
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return fmt.Errorf("error marshalling JSON: %w", err)
	}

	dir := filepath.Dir(filePath)
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		err = os.MkdirAll(dir, 0755)
		if err != nil {
			return fmt.Errorf("error creating directory: %w", err)
		}
	}

	err = os.WriteFile(filePath, jsonData, 0644)
	if err != nil {
		return fmt.Errorf("error writing file: %w", err)
	}

	log.Printf("Successfully wrote JSON data to %s", filePath)

	return nil
}
