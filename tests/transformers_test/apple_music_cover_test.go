package transformers

import (
	"testing"

	"github.com/EliJaghab/tunemeld/transformers"
)

func TestGetAlbumURL_Success(t *testing.T) {
	testURL := "https://music.apple.com/us/album/happier-feat-clementine-douglas/1721072384?i=1721072870"
	expectedURL := "https://is1-ssl.mzstatic.com/image/thumb/Music116/v4/9d/b5/c7/9db5c79b-d70a-d617-a8fa-6599b6094eac/5054197941139.jpg/296x296bb-60.jpg"

	resultURL, err := transformers.GetAlbumURL(testURL)

	if err != nil {
		t.Errorf("Failed to get album URL: %v", err)
	}

	if resultURL != expectedURL {
		t.Errorf("Expected URL %s, got %s", expectedURL, resultURL)
	}
}
