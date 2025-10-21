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
- Cloudflare KV cache clears **only on Saturdays** (weekday=5) to avoid API rate limits
- Monday-Friday: reuses cached data

**Output**: 16 RawPlaylistDataModel records (4 genres × 4 services - 4 missing combinations)

**Key files**:

- `core/models/playlist.py:15-60` - RawPlaylistDataModel
- `core/services/` - API scrapers (spotify_service.py, apple_music_service.py, soundcloud_service.py)

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

**Key files**:

- `core/models/playlist.py:62-110` - PlaylistModel
- `core/models/playlist.py:112-162` - ServiceTrackModel
- `core/services/spotify_service.py:162-197` - get_isrc_from_spotify()

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
- Uses `update_or_create(isrc=...)` to update existing tracks

**Bug Fixed (Oct 21, 2025)**:

- Previously filtered out tracks with YouTube+SoundCloud URLs
- Caused Apple Music/Spotify URLs to not sync for existing tracks
- Now processes all playlist ISRCs to keep service URLs synchronized

**Output**: ~600 TrackModel records with URLs across all services

**Key files**:

- `core/models/track.py` - TrackModel
- `core/services/youtube_service.py` - get_youtube_url()
- `core/services/soundcloud_service.py` - get_soundcloud_url()

---

### Step D: Create Aggregate Playlist (`d_aggregate.py`)

**Purpose**: Create TuneMeld aggregate playlist by combining tracks across all services

**What it does**:

- Finds tracks appearing on multiple service playlists (service_count > 1)
- Calculates aggregate scores based on:
  - Position on each service playlist
  - Number of services featuring the track
- Creates aggregate playlist per genre
- Updates `TrackModel.aggregate_rank` and `TrackModel.aggregate_score`

**Scoring Formula**:

```python
position_score = sum((max_positions - position) for each service)
service_bonus = service_count * 10
aggregate_score = position_score + service_bonus
```

**Output**: ~200-300 tracks per genre with aggregate rankings

**Key files**:

- `core/models/track.py` - TrackModel (aggregate_rank, aggregate_score fields)

---

### Step 6: Clear and Warm Cache (`e_clear_and_warm_track_cache.py`)

**Purpose**: Warm Redis cache with GraphQL query results for fast API responses

**What it does**:

- **Clears** Redis cache (GQL_PLAYLIST, GQL_PLAY_COUNT, GQL_PLAYLIST_METADATA)
- **Executes** GraphQL queries for all genre/service combinations
- **Populates** Redis Cloud cache with results
- Enables <200ms API responses (vs 10+ seconds without cache)

**Cache Keys**:

- `CachePrefix.GQL_PLAYLIST:{genre}:{service}` - Full playlist data
- `CachePrefix.GQL_PLAY_COUNT:{isrc}` - Play count aggregations
- `CachePrefix.GQL_PLAYLIST_METADATA:{genre}:{service}` - Playlist metadata

**Why This Matters**:

- Serverless functions don't cache on startup (stateless)
- Redis Cloud persists across invocations
- Cache warming ensures production API stays fast

**Output**: Warmed Redis cache for all frontend queries

**Key files**:

- `core/utils/redis_cache.py` - Redis cache utilities
- `gql/schema.py` - GraphQL resolvers

---

## Cache Architecture

### CloudflareKV Cache

**Purpose**: Cache external API responses (RapidAPI, YouTube, Spotify ISRC lookups)
**Clearing**: Only on Saturdays (scheduled runs)
**TTL**: 7 days for playlists, no expiration for ISRCs/URLs

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

## Running ETL

### Production (GitHub Actions)

```bash
# Trigger via workflow_dispatch
gh workflow run playlist_etl.yml --ref master
```

### Local Development

```bash
# Full pipeline
make run-playlist-etl

# Individual steps
python manage.py shell -c "from core.management.commands.playlist_etl_modules.a_raw_playlist import Command; Command().handle()"
python manage.py shell -c "from core.management.commands.playlist_etl_modules.b_playlist_service_track import Command; Command().handle()"
python manage.py shell -c "from core.management.commands.playlist_etl_modules.c_track import Command; Command().handle()"
python manage.py shell -c "from core.management.commands.playlist_etl_modules.d_aggregate import Command; Command().handle()"
```

---

## Debugging

### Check raw data timestamps

```python
from core.models.playlist import RawPlaylistDataModel
for raw in RawPlaylistDataModel.objects.all():
    print(f"{raw.service.name}/{raw.genre.name}: Created {raw.created_at}, Updated {raw.updated_at}")
```

### Check ServiceTrack updates

```python
from core.models.playlist import ServiceTrackModel
from core.models.genre_service import ServiceModel, GenreModel

service = ServiceModel.objects.get(name='apple_music')
genre = GenreModel.objects.get(name='dance')
latest = ServiceTrackModel.objects.filter(service=service, genre=genre).order_by('-updated_at').first()
print(f"Latest update: {latest.updated_at}")
```

### Check Track URL synchronization

```python
from core.models.track import TrackModel

track = TrackModel.objects.get(isrc='QT47L2500045')  # Example ISRC
print(f"Spotify: {track.spotify_url}")
print(f"Apple Music: {track.apple_music_url}")
print(f"SoundCloud: {track.soundcloud_url}")
print(f"YouTube: {track.youtube_url}")
print(f"Updated: {track.updated_at}")
```

---

## Common Issues

### Missing service icons on frontend

**Symptom**: Track shows only one service icon when it should show multiple
**Cause**: Step C filtered out tracks incorrectly, preventing service URL sync
**Fix**: Commit 2d60877 (Oct 21, 2025) - process all playlist ISRCs

### Stale raw data

**Symptom**: RawPlaylistDataModel `updated_at` not changing
**Cause**: Cloudflare cache hit (cache only clears on Saturdays)
**Expected**: Monday-Friday reuse cached data to avoid API rate limits

### ServiceTracks not updating

**Symptom**: ServiceTrackModel timestamps stuck on old date
**Cause**: Check if Step B is actually running in production (review GitHub Actions logs)
**Debug**: Run locally and compare timestamps

---

## Related Files

- `/Users/eli/github/tunemeld/backend/core/constants.py` - GENRE_CONFIGS (playlist URLs)
- `/Users/eli/github/tunemeld/backend/gql/schema.py` - GraphQL schema
- `/Users/eli/github/tunemeld/backend/core/utils/cloudflare_cache.py` - Cache clearing logic
- `/Users/eli/github/tunemeld/.github/workflows/playlist_etl.yml` - GitHub Actions workflow
