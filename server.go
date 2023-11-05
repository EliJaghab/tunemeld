package main

import (
	"net/http"
	"time"
)

func main() {
	server := &http.Server{
		Addr:              ":8000",
		Handler:           nil,              
		IdleTimeout:       20 * time.Minute, 
		ReadHeaderTimeout: 10 * time.Second, 
	}

	err := server.ListenAndServe()
	if err != nil {
		panic(err)
	}
}
