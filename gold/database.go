package gold

import (
	"database/sql"
	"fmt"
	"log"

	"strings"

	"github.com/lib/pq"

	"github.com/EliJaghab/tunemeld/config"
)

func GetTracksDatabaseConnection() (*sql.DB, error) {
	defaultDb, err := GetDatabaseConnection(config.PostgresConnectionString)
	if err != nil {
		return nil, fmt.Errorf("failed to get database connection: %w", err)
	}

	err = DropAndCreateDatabase(defaultDb, "tracks")
	if err != nil {
		return nil, fmt.Errorf("failed to drop and create database: %w", err)
	}

	tracksDb, err := GetDatabaseConnection(config.TracksConnectionString)
	if err != nil {
		return nil, fmt.Errorf("failed to get database connection: %w", err)
	}
	return tracksDb, nil
}

func GetDatabaseConnection(connStr string) (*sql.DB, error) {
	db, err := sql.Open("postgres", connStr)
	if err != nil {
		return nil, fmt.Errorf("error opening database connection: %w", err)
	}

	if err = db.Ping(); err != nil {
		return nil, fmt.Errorf("error pinging database: %w", err)
	}

	return db, nil
}

func DropAndCreateDatabase(db *sql.DB, dbName string) error {
	_, err := db.Exec("DROP DATABASE IF EXISTS " + dbName)
	if err != nil {
		return fmt.Errorf("failed to drop database %s: %w", dbName, err)
	}

	_, err = db.Exec("CREATE DATABASE " + dbName)
	if err != nil {
		return fmt.Errorf("failed to create database %s: %w", dbName, err)
	}

	return nil
}

func printViewContents(db *sql.DB, viewName string) {
	printRowCount(db, viewName)
	log.Printf("View contents for %s:", viewName)
	// nolint:gosec // tableName is safely quoted
	query := "SELECT * FROM " + pq.QuoteIdentifier(viewName)

	rows, err := db.Query(query)
	if err != nil {
		log.Fatalf("Failed to execute query: %v", err)
	}
	defer rows.Close()

	columns, err := rows.Columns()
	if err != nil {
		log.Fatalf("Failed to get columns: %v", err)
	}

	values := make([]interface{}, len(columns))
	valuePtrs := make([]interface{}, len(columns))
	for i := range values {
		valuePtrs[i] = &values[i]
	}

	fmt.Println(strings.Join(columns, "\t"))

	for rows.Next() {
		err := rows.Scan(valuePtrs...)
		if err != nil {
			log.Fatalf("Failed to scan row: %v", err)
		}

		for i, val := range values {
			strVal := fmt.Sprintf("%v", val)
			if len(strVal) > 10 {
				values[i] = strVal[:7] + "..."
			}
		}
		fmt.Println(values...)
	}
}

func printRowCount(db *sql.DB, tableName string) {
	var rowCount int
	query := "SELECT COUNT(*) FROM " + pq.QuoteIdentifier(tableName)

	err := db.QueryRow(query).Scan(&rowCount)
	if err != nil {
		log.Fatalf("Failed to query row count: %v", err)
	}

	fmt.Printf("Row count in %s: %d\n", tableName, rowCount)
}
