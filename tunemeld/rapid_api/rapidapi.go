package rapidapi

import (
	"fmt"
	"io"
	"net/http"
    "os"
)

type RapidAPIClient struct {
	apiKey string
}

func NewRapidAPIClient() *RapidAPIClient {
    apiKey := os.Getenv("X_RapidAPI_Key")
	return &RapidAPIClient{apiKey: apiKey}
}

func (client *RapidAPIClient) MakeRequest(url, host string) {
	req, _ := http.NewRequest("GET", url, nil)
	req.Header.Add("X-RapidAPI-Key", client.apiKey)
	req.Header.Add("X-RapidAPI-Host", host)

	res, _ := http.DefaultClient.Do(req)
	defer res.Body.Close()

	body, _ := io.ReadAll(res.Body)
	fmt.Println(res)
	fmt.Println(string(body))
}
