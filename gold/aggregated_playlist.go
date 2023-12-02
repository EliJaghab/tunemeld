package gold

import (
	"database/sql"
	"fmt"
	"log"

	"github.com/lib/pq"

	"github.com/EliJaghab/tunemeld/config"
)

func Transform(
	soundCloudTracks, spotifyTracks, appleMusicTracks []config.Track,
) ([]config.GoldTrack, error) {
	tracksDb, err := GetTracksDatabaseConnection()
	if err != nil {
		return nil, fmt.Errorf("failed to get database connection: %w", err)
	}
	defer tracksDb.Close()

	err = createAllTracksTable(tracksDb)
	if err != nil {
		return nil, fmt.Errorf("failed to create all_tracks table: %w", err)
	}

	err = insertTracks(tracksDb, soundCloudTracks)
	if err != nil {
		return nil, fmt.Errorf("failed to insert tracks: %w", err)
	}

	err = insertTracks(tracksDb, spotifyTracks)
	if err != nil {
		return nil, fmt.Errorf("failed to insert tracks: %w", err)
	}

	err = insertTracks(tracksDb, appleMusicTracks)
	if err != nil {
		return nil, fmt.Errorf("failed to insert tracks: %w", err)
	}

	err = createTrackSimilarityView(tracksDb)
	if err != nil {
		return nil, fmt.Errorf("failed to create track_similarity view: %w", err)
	}

	err = createMatchesView(tracksDb)
	if err != nil {
		return nil, fmt.Errorf("failed to create matches view: %w", err)
	}

	goldTracks, err := getGoldTracks(tracksDb)
	if err != nil {
		return nil, fmt.Errorf("failed to get gold tracks: %w", err)
	}

	return goldTracks, nil
}

func createAllTracksTable(db *sql.DB) error {
	_, err := db.Exec(`
		CREATE TABLE IF NOT EXISTS all_tracks (
			name VARCHAR(255),
			artist VARCHAR(255),
			link VARCHAR(255),
			rank INT,
			album_url VARCHAR(255),
			source VARCHAR(50)
		);
	`)
	if err != nil {
		return fmt.Errorf("failed to create table in 'tracks' database: %v", err)
	}
	return nil
}

func insertTracks(db *sql.DB, tracks []config.Track) error {
	stmt, err := db.Prepare(`
		INSERT INTO all_tracks 
		(name, artist, link, rank, album_url, source) 
		VALUES ($1, $2, $3, $4, $5, $6)
	`)

	if err != nil {
		return fmt.Errorf("failed to prepare statement: %v", err)
	}
	defer stmt.Close()

	for _, track := range tracks {

		_, err := stmt.Exec(track.Name, track.Artist, track.Link, track.Rank, track.AlbumURL, track.Source.String())
		if err != nil {
			return fmt.Errorf("failed to execute statement: %v", err)
		}
	}
	return nil
}

func createTrackSimilarityView(db *sql.DB) error {
	_, err := db.Exec("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
	if err != nil {
		log.Fatalf("Failed to create pg_trgm extension: %v", err)
	}

	_, err = db.Exec(`
	CREATE OR REPLACE VIEW track_pairs AS
	WITH track_similarity AS (
		SELECT
			sc.name AS sc_name, sc.artist AS sc_artist,
			sc.link AS sc_link, sc.rank AS sc_rank,
			sc.album_url AS sc_album_url, sc.source AS sc_source,
	
			sp.name AS sp_name, sp.artist AS sp_artist,
			sp.link AS sp_link, sp.rank AS sp_rank,
			sp.album_url AS sp_album_url, sp.source AS sp_source,
	
			am.name AS am_name, am.artist AS am_artist,
			am.link AS am_link, am.rank AS am_rank,
			am.album_url AS am_album_url, am.source AS am_source,
	
			similarity(concat(sc.name, sc.artist), concat(sp.name, sp.artist)) AS sim_sc_sp,
			similarity(concat(sc.name, sc.artist), concat(am.name, am.artist)) AS sim_sc_am,
			similarity(concat(sp.name, sp.artist), concat(am.name, am.artist)) AS sim_sp_am
		FROM 
			all_tracks sc
		CROSS JOIN 
			all_tracks sp
		CROSS JOIN 
			all_tracks am
		WHERE 
			sc.source = 'soundcloud' AND 
			sp.source = 'spotify' AND 
			am.source = 'apple_music'
	)
	
	SELECT
		*,
		-- Boolean flags for similarity threshold
		sim_sc_sp > 0.7 AS match_sc_sp,
		sim_sc_am > 0.7 AS match_sc_am,
		sim_sp_am > 0.7 AS match_sp_am,
		
		-- Determine if a track is on all three services
		(sim_sc_sp > 0.7 AND sim_sc_am > 0.7 AND sim_sp_am > 0.7) AS match_all_three,
		-- Determine if a track is on any two services
		(sim_sc_sp > 0.7 AND sim_sc_am > 0.7) OR
		(sim_sc_sp > 0.7 AND sim_sp_am > 0.7) OR
		(sim_sc_am > 0.7 AND sim_sp_am > 0.7) AS match_any_two
	FROM 
		track_similarity;
	
    `)
	if err != nil {
		log.Fatalf("Failed to create track_pairs view: %v", err)
	}
	printViewContents(db, "all_tracks")
	printViewContents(db, "track_pairs")
	return nil

}

func createMatchesView(db *sql.DB) error {
	// Prioritize soundcloud values, then spotify for the row values if there is a match
	_, err := db.Exec(`
	CREATE OR REPLACE VIEW matches AS
		SELECT
			CASE
				WHEN match_all_three THEN sc_name
				WHEN match_sc_sp THEN sc_name
				ELSE sp_name
			END AS name,
			CASE
				WHEN match_all_three THEN sc_artist
				WHEN match_sc_sp THEN sc_artist
				ELSE sp_artist
			END AS artist,
			CASE
				WHEN match_all_three THEN sc_link
				WHEN match_sc_sp THEN sc_link
				ELSE sp_link
			END AS link,
			CASE
				WHEN match_all_three THEN sc_rank
				WHEN match_sc_sp THEN sc_rank
				ELSE sp_rank
			END AS rank,
			CASE
				WHEN match_all_three THEN sc_album_url
				WHEN match_sc_sp THEN sc_album_url
				ELSE sp_album_url
			END AS album_url,
			CASE
				WHEN match_sc_sp OR match_sc_am THEN sc_source
				ELSE sp_source
			END AS source,
			CASE
				WHEN match_sc_sp OR match_sc_am THEN ARRAY[am_source, sp_source]
				WHEN match_sp_am THEN ARRAY[sc_source, sp_source]
			ELSE ARRAY[sc_source, am_source]
		END AS additional_sources
	FROM
		track_pairs
	WHERE
		match_all_three OR match_any_two
	ORDER BY am_rank, sp_rank, sc_rank;
    `)

	if err != nil {
		return fmt.Errorf("failed to create prioritized_tracks view: %w", err)
	}
	return nil
}

func getGoldTracks(db *sql.DB) ([]config.GoldTrack, error) {
	rows, err := db.Query(`
		SELECT
			name,
			artist,
			link,
			rank,
			album_url,
			source,
			additional_sources
		FROM
		matches;
	`)
	if err != nil {
		return nil, fmt.Errorf("failed to query prioritized_tracks view: %w", err)
	}
	defer rows.Close()

	var results []config.GoldTrack
	for rows.Next() {
		var (
			trackName         string
			artist            string
			link              string
			rank              int
			albumURL          string
			source            string
			additionalSources []string
		)

		if err := rows.Scan(&trackName, &artist, &link, &rank, &albumURL, &source, pq.Array(&additionalSources)); err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}

		var trackSources []config.TrackSource
		for _, src := range additionalSources {
			source, err := config.ParseTrackSource(src)
			if err != nil {
				return nil, fmt.Errorf("failed to parse source: %w", err)
			}
			trackSources = append(trackSources, source)
		}

		baseSource, err := config.ParseTrackSource(source)
		if err != nil {
			return nil, fmt.Errorf("failed to parse source: %w", err)
		}

		gt := config.GoldTrack{
			Track: config.Track{
				Name:     trackName,
				Artist:   artist,
				Link:     link,
				Rank:     rank,
				AlbumURL: albumURL,
				Source:   baseSource,
			},
			AdditionalSources: trackSources,
		}

		results = append(results, gt)
	}

	return results, nil
}
