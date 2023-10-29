package main

import (
    "net/http"
    "log"
)

func main() {
    // Set the directory to serve files from
    fs := http.FileServer(http.Dir("."))
    http.Handle("/", fs)

    // Start the server on port 8000
    log.Println("Serving on port 8000...")
    err := http.ListenAndServe(":8000", nil)
    if err != nil {
        log.Fatal(err)
    }
}
