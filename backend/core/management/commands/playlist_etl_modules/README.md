# TuneMeld ETL Pipeline

Complete playlist data extraction, transformation, and loading pipeline that runs daily via GitHub Actions.

## Pipeline Overview

```
Step A: Raw Extract → Step B: ServiceTracks → Step C: Tracks → Step D: Aggregate → Step 6: Cache Warming
```

## Pipeline Steps

### Step A: Raw Playlist Extraction (`a_raw_playlist.py`)

**Purpose**: Fetch raw playlist data from external APIs (Spotify, Apple Music, SoundCloud)

**What it does**:

- Scrapes playlist data from RapidAPI (Apple Music, SoundCloud) and Spotify API
- Stores raw JSON responses in `RawPlaylistDataModel`
- **IMPORTANT**: Cloudflare cache clearing applies **ONLY to raw playlists**
  - Raw playlists clear **only on Saturdays** (weekday=5) to avoid API rate limits
  - Monday-Friday: reuses cached playlist data
  - All other cached data (ISRCs, YouTube URLs, SoundCloud URLs, etc.) **never expires**

**Output**: 16 RawPlaylistDataModel records (4 genres × 4 services - 4 missing combinations)

---

### Step B: Create ServiceTracks (`b_playlist_service_track.py`)

**Purpose**: Normalize raw API data into ServiceTrackModel entries with ISRC matching

**What it does**:

- Parses raw JSON data from Step A
- Creates/updates `ServiceTrackModel` entries (one per playlist position)
- Deletes old playlists before recreating (fresh state each run)
- Uses Spotify API to fetch ISRCs for tracks missing them (Apple Music, SoundCloud)
- Links ServiceTracks to PlaylistModel for position tracking

**ISRC Lookup Priority**:

1. Extract from raw data (Spotify includes ISRCs)
2. Search Spotify API for Apple Music/SoundCloud tracks
3. Skip tracks without ISRCs

**Output**: ~600 ServiceTrackModel records (50-75 tracks per playlist × 16 playlists)

---

### Step C: Create Canonical Tracks (`c_track.py`)

**Purpose**: Create canonical TrackModel records with URLs for all services

**What it does**:

- **CRITICAL**: Processes **ALL** ISRCs from current playlists (no filtering)
- Groups ServiceTrackModels by ISRC
- Chooses primary track (priority: Spotify > Apple Music > SoundCloud)
- Copies service URLs from ServiceTrackModels to TrackModel:
  - Spotify URL: from Spotify ServiceTrackModel
  - Apple Music URL: from Apple Music ServiceTrackModel
  - SoundCloud URL: from SoundCloud ServiceTrackModel OR independent lookup
  - YouTube URL: independent lookup via YouTube API
- Updates existing tracks to keep service URLs synchronized

**Output**: ~600 TrackModel records with URLs across all services

---

### Step D: Create Aggregate Playlist (`d_aggregate.py`)

**Purpose**: Create TuneMeld aggregate playlist by combining tracks across all services

**What it does**:

- Finds tracks appearing on multiple service playlists (service_count > 1)
- Calculates aggregate scores based on:
  - Position on each service playlist
  - Number of services featuring the track
- Creates aggregate playlist per genre
- Updates TrackModel aggregate_rank and aggregate_score fields

**Output**: ~200-300 tracks per genre with aggregate rankings

---

### Step 6: Clear and Warm Cache (`e_clear_and_warm_track_cache.py`)

**Purpose**: Warm Redis cache with GraphQL query results for fast API responses

**What it does**:

- **Clears** Redis cache (GQL_PLAYLIST, GQL_PLAY_COUNT, GQL_PLAYLIST_METADATA)
- **Executes** GraphQL queries for all genre/service combinations
- **Populates** Redis Cloud cache with results
- Enables <200ms API responses (vs 10+ seconds without cache)
- Serverless functions don't cache on startup (stateless)
- Redis Cloud persists across invocations

**Output**: Warmed Redis cache for all frontend queries

---

## Cache Architecture

### CloudflareKV Cache

**Purpose**: Cache external API responses (RapidAPI, YouTube, Spotify ISRC lookups)

**Cache Clearing Policy**:

- **Raw Playlists ONLY**: Clear on Saturdays (scheduled runs)
- **Everything Else NEVER Clears**: ISRCs, YouTube URLs, SoundCloud URLs, album covers, etc. persist permanently
- **Why**: Avoid hitting API rate limits while keeping fresh playlist positions weekly

### Redis Cache

**Purpose**: Cache GraphQL query results for frontend
**Clearing**: Daily during Step 6
**TTL**: Set per cache prefix (GQL_PLAYLIST, etc.)

---

## Database Models

```
RawPlaylistDataModel (Step A output)
  ↓ parsed by
ServiceTrackModel (Step B output)
  ↓ grouped by ISRC
TrackModel (Step C output)
  ↓ filtered by service_count > 1
TuneMeld Aggregate Playlist (Step D output)
```

---

## Running ETL Locally

```bash
# Full pipeline
make run-playlist-etl
```
