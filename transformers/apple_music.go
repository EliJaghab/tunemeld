package transformers

import (
	"fmt"
	"log"
	"strconv"
	"net/http"
	"time"
	"github.com/PuerkitoBio/goquery"

	"github.com/EliJaghab/tunemeld/config"
)

type AppleMusicTransformer struct{}

func (t *AppleMusicTransformer) Execute(data []map[string]interface{}) ([]config.Track, error) {
	log.Println("Executing AppleMusicTransformer...")

	if len(data) == 0 {
		return nil, fmt.Errorf("data is empty")
	}

	albumDetailsInterface, ok := data[0]["album_details"]
	if !ok {
		return nil, fmt.Errorf("album details not found in data")
	}

	albumDetails, ok := albumDetailsInterface.(map[string]interface{})
	if !ok { 
		return nil, fmt.Errorf("invalid album details format")
	}

	var tracks []config.Track
	for rankStr, trackDataInterface := range albumDetails {
		rank, err := strconv.Atoi(rankStr)
		if err != nil {
			log.Printf("Warning: Skipping rank %s due to conversion error: %v", rankStr, err)
			continue
		}

		rank = rank + 1 // Rank is 1-indexed, array is 0-indexed

		trackData, ok := trackDataInterface.(map[string]interface{})
		if !ok {
			return nil, fmt.Errorf("invalid track data format")
		}

		trackName, ok := trackData["name"].(string)
		if !ok {
			return nil, fmt.Errorf("invalid track name format")
		}

		artistName, ok := trackData["artist"].(string)
		if !ok {
			return nil, fmt.Errorf("invalid artist name format")
		}

		link, ok := trackData["link"].(string)
		if !ok {
			return nil, fmt.Errorf("invalid link format")
		}

		albumURL, err := GetAlbumURL(link)
		if err != nil {
			log.Printf("Warning: failed to get album URL for track %s by artist %s: %v", trackName, artistName, err)
		}

		track := config.Track{
			Name:     trackName,
			Artist:   artistName,
			Link:     link,
			Rank:     rank,
			AlbumURL: albumURL,
			Source:   config.SourceAppleMusic,
		}
		tracks = append(tracks, track)
	}

	log.Printf("Successfully transformed %d tracks", len(tracks))
	return tracks, nil
}


func GetAlbumURL(link string) (string, error) {
	client := &http.Client{
		Timeout: 30 * time.Second,
	}
	
	// Send an HTTP GET request to the link
	resp, err := client.Get(link)
	if err != nil {
		return "", fmt.Errorf("failed to send HTTP request: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("HTTP request returned non-200 status: %d", resp.StatusCode)
	}

	// Parse the HTML response
	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to parse HTML document: %v", err)
	}

	// Query the document to find the specific tag and attribute
	srcset, exists := doc.Find("source[type='image/jpeg']").Attr("srcset")
	if !exists {
		return "", fmt.Errorf("album cover URL not found")
	}

	// The srcset attribute may contain multiple URLs; extract the first one
	url := firstURLFromSrcset(srcset)
	if url == "" {
		return "", fmt.Errorf("no URL found in srcset attribute")
	}

	return url, nil
}

// firstURLFromSrcset extracts the first URL from a srcset attribute value
func firstURLFromSrcset(srcset string) string {
	var url string
	fmt.Sscanf(srcset, "%s ", &url)
	return url
}
