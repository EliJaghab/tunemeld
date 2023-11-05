package main

import (
	"net/http"
	"time"
)

func main() {
	server := &http.Server{
		Addr:              ":8000",
		Handler:           nil,              // Uses http.DefaultServeMux
		IdleTimeout:       20 * time.Minute, // 20 minutes of idleness before closing the connection
		ReadHeaderTimeout: 10 * time.Second, // 10 seconds to read the request headers
	}

	err := server.ListenAndServe()
	if err != nil {
		panic(err)
	}
}
