package service

import json

func parseJSON(data []byte) (map[string]interface{}, error) {
    var result map[string]interface{}
    err := json.Unmarshal(data, &result)
    if err != nil {
        return nil, fmt.Errorf("error parsing JSON: %w", err)
    }
    return result, nil
}