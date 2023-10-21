// +build lambda

package main

import (
    "context"
    "go_migration/rapidapi"
    "github.com/aws/aws-lambda-go/lambda"
)

func handler(ctx context.Context) {
    client := rapidapi.NewClient()
    run(client)
}

func main() {
    lambda.Start(handler)
}
