# TuneMeld Data Engineering Guide

## Quick Reference

**Production Database**: PostgreSQL (via `DATABASE_URL` in `.env.production`)
**Local Database**: SQLite (via `DATABASE_URL` in `.env.dev`)
**Caches**: CloudflareKV (ETL data) + Redis Cloud (GraphQL responses)
**ETL Schedule**: Daily at 2:00 AM UTC (Play Count) and 2:30 AM UTC (Playlist)

## Bug Fix & Production Deployment Workflow

### Step 1: Reproduce Bug Locally

```bash
# Sync production data to local
make sync-prod

# Start local servers
make serve-backend  # Terminal 1
make serve-frontend # Terminal 2

# Reproduce the bug locally with production data
```

### Step 2: Identify Root Cause

```bash
# Use Django shell to investigate
cd backend && python manage.py shell
```

```python
# Example: Debug missing YouTube URLs
from core.models import TrackModel

tracks_no_youtube = TrackModel.objects.filter(youtube_url__isnull=True)
print(f"Tracks missing YouTube: {tracks_no_youtube.count()}")

# Check raw data to see if issue is in extraction or transformation
from core.models import RawPlaylistDataModel
raw = RawPlaylistDataModel.objects.first()
print(raw.raw_json_data)  # Inspect raw API response
```

### Step 3: Write & Test Fix Locally

```bash
# Edit the buggy file (e.g., playlist_etl_modules/c_track.py)
# Make your code changes

# Test with limited dataset first
cd backend
python manage.py playlist_etl  # Or play_count, audio_features_etl

# Verify fix worked
python manage.py shell
```

```python
# Verify the fix
from core.models import TrackModel
tracks_no_youtube = TrackModel.objects.filter(youtube_url__isnull=True).count()
print(f"Tracks missing YouTube after fix: {tracks_no_youtube}")  # Should be 0 or reduced
```

### Step 4: Format & Commit Changes

```bash
# REQUIRED: Run pre-commit hooks before committing
make format

# Commit changes
git add backend/core/management/commands/playlist_etl_modules/c_track.py
git commit -m "fix: resolve YouTube URL extraction bug for tracks

- Fixed issue where tracks were missing YouTube URLs
- Added better error handling in track creation step
- Tested locally with production data"

# Push to GitHub
git push origin master
```

### Step 5: Automatic Deployment

**Backend (Vercel)**:

- Push to `master` triggers automatic Vercel deployment
- Vercel builds and deploys serverless functions
- GraphQL API updated with fixed code
- **No manual action needed**

**ETL (GitHub Actions)**:

- ETL runs daily at scheduled times (2:00 AM, 2:30 AM UTC)
- **OR** manually trigger ETL to apply fix immediately (see Step 6)

### Step 6: Manually Trigger ETL (Apply Fix Immediately)

**Option 1: GitHub Actions UI**

1. Go to https://github.com/EliJaghab/tunemeld/actions
2. Select "Playlist ETL" or "Historical Track Play Count ETL"
3. Click "Run workflow" (top right)
4. Choose options:
   - For playlist bugs: Check "force_refresh" to bypass cache
   - For play count bugs: Leave defaults
5. Click "Run workflow"
6. Monitor progress in Actions tab

**Option 2: Command Line (GitHub CLI)**

```bash
# Trigger Playlist ETL with force refresh
gh workflow run playlist_etl.yml -f force_refresh=true

# Trigger Play Count ETL
gh workflow run play_count.yml

# Check workflow status
gh run list --workflow=playlist_etl.yml --limit 1
```

### Step 7: Verify Fix in Production

**Check Deployment Status**:

```bash
# Backend deployment (Vercel)
vercel ls tunemeld --prod

# ETL completion (GitHub Actions)
gh run list --workflow=playlist_etl.yml --limit 1
```

**Verify Data Fix**:

```bash
# Sync production data again to verify fix
make sync-prod

cd backend && python manage.py shell
```

```python
# Verify the fix in production data
from core.models import TrackModel

tracks_no_youtube = TrackModel.objects.filter(youtube_url__isnull=True).count()
print(f"Production tracks missing YouTube: {tracks_no_youtube}")  # Should be fixed

# Check frontend API response
import requests
response = requests.post(
    "https://tunemeld.com/api/graphql",
    json={"query": "{ tracks(genre: \"hip-hop\", service: \"spotify\") { trackName youtubeUrl } }"}
)
print(response.json())  # Verify YouTube URLs present
```

**Test Frontend**:

1. Visit https://tunemeld.com
2. Select genre and service affected by bug
3. Verify fix is working (e.g., tracks show YouTube URLs, no missing data)

### Step 8: Monitor for Regressions

```bash
# Watch GitHub Actions for next scheduled run
# Ensure bug doesn't reoccur

# Check Vercel logs for errors
vercel logs tunemeld --prod
```

### Common Deployment Scenarios

**Scenario 1: ETL Logic Bug (Playlist Extraction)**

- Fix code in `backend/core/management/commands/playlist_etl_modules/`
- Commit, push to master
- Manually trigger "Playlist ETL" workflow with `force_refresh=true`
- Verify in production after ~15-30 minutes

**Scenario 2: GraphQL API Bug (Frontend Query)**

- Fix code in `backend/core/schema.py` or `backend/core/graphql/`
- Commit, push to master
- Vercel automatically deploys in ~2 minutes
- Clear Redis cache if needed: Run "Clear and Warm Cache" workflow
- Verify immediately at https://tunemeld.com/api/graphql

**Scenario 3: Data Model Bug (Database Schema)**

- Create migration: `make makemigrations`
- Test migration locally: `make migrate-dev`
- Commit migration file, push to master
- GitHub Actions automatically applies migration before next ETL run
- **OR** manually trigger ETL to apply migration immediately

**Scenario 4: Cache Bug (Redis/CloudflareKV)**

- Fix cache logic in `backend/core/utils/redis_cache.py` or `cloudflare_cache.py`
- Commit, push to master
- Trigger "Clear and Warm Cache" workflow to clear Redis
- For CloudflareKV: Trigger Playlist ETL with `force_refresh=true`

### Emergency Rollback

**If deployment breaks production**:

1. **Revert commit**:

```bash
git revert HEAD
git push origin master
```

2. **Vercel auto-deploys reverted code** (~2 minutes)

3. **Re-run ETL** if data was corrupted:

```bash
# Restore from backup if needed (contact DBA)
# Or re-run ETL to regenerate data
gh workflow run playlist_etl.yml -f force_refresh=true
```

4. **Verify production restored**:

```bash
make sync-prod
# Check data locally
```

### Deployment Checklist

Before pushing bug fix to production:

- [ ] Reproduced bug locally with `make sync-prod`
- [ ] Identified root cause in code (not just symptoms)
- [ ] Fixed code and tested locally
- [ ] Ran `make format` (pre-commit hooks)
- [ ] Committed with descriptive message
- [ ] Pushed to `master` branch
- [ ] Monitored Vercel deployment (if backend change)
- [ ] Manually triggered ETL (if ETL change)
- [ ] Verified fix in production with `make sync-prod`
- [ ] Tested frontend at https://tunemeld.com
- [ ] Monitored next scheduled ETL run for regressions

## ETL Pipelines

### Playlist ETL (`make run-playlist-etl`)

**Purpose**: Extract playlist and track data from Spotify, YouTube, Apple Music, SoundCloud

**Pipeline Steps**:

1. **Genre/Service Setup** - Ensures genre and service records exist in database
2. **Raw Playlist Extraction** - Fetches playlist data from external APIs (RapidAPI, Spotify, SoundCloud)
   - Cached in CloudflareKV to avoid API rate limits
   - Use `--force-refresh` flag to bypass cache and pull fresh data
3. **Service Track Creation** - Normalizes raw playlist data into service-specific tracks
4. **Canonical Track Creation** - Deduplicates tracks across services, fetches YouTube URLs
5. **Track Aggregation** - Computes aggregate stats (trending percentages, rank changes)
6. **Cache Warming** - Populates Redis with GraphQL query responses

**Schedule**: Daily at 2:30 AM UTC (GitHub Actions)

**Commands**:

```bash
make run-playlist-etl              # Full production ETL
make run-playlist-etl-force-refresh # Bypass CloudflareKV cache, pull fresh API data
```

**Files**:

- `/backend/core/management/commands/playlist_etl.py` - Main orchestrator
- `/backend/core/management/commands/playlist_etl_modules/` - Step implementations

### Play Count ETL (`make run-play-count-etl`)

**Purpose**: Extract daily play counts from Spotify and YouTube for trending analysis

**Pipeline Steps**:

1. **Genre/Service Setup** - Ensures genre and service records exist
2. **Historical Play Count Extraction** - Scrapes current play counts from Spotify/YouTube
   - Creates `HistoricalTrackPlayCountModel` records with today's date
3. **Aggregate Play Count Computation** - Calculates weekly percentage changes
   - Compares today's play count to 7 days ago
   - Stores in `AggregateTrackPlayCountModel`
4. **Cache Warming** - Populates Redis with play count GraphQL responses

**Schedule**: Daily at 2:00 AM UTC (GitHub Actions)

**Commands**:

```bash
make run-play-count-etl          # Full production ETL
make test-play-count-etl         # Test with 10 tracks only
```

**Files**:

- `/backend/core/management/commands/play_count.py` - Main orchestrator
- `/backend/core/management/commands/play_count_modules/` - Step implementations

### Audio Features ETL (`make run-audio-features-etl`)

**Purpose**: Extract audio features (BPM, key, energy, danceability) from Spotify and Genius lyrics

**Commands**:

```bash
make run-audio-features-etl      # Full production ETL
make test-audio-features-etl     # Test with 10 tracks only
```

**Files**:

- `/backend/core/management/commands/audio_features_etl.py` - Main orchestrator

## Database Access

### Connect to Production Database

**Option 1: Sync Production to Local** (Recommended for analysis)

```bash
make sync-prod    # Syncs PostgreSQL data to local SQLite + Redis cache
```

This command:

- Dumps production PostgreSQL database to JSON
- Loads data into local SQLite database
- Syncs production Redis cache to local Redis (`localhost:6379/1`)
- Safe for analysis without affecting production

**Option 2: Backfill Missing CloudflareKV Cache Keys**

```bash
cd backend
python manage.py backfill_cloudflare_cache --dry-run  # Preview what would be backfilled
python manage.py backfill_cloudflare_cache             # Backfill missing keys
```

This command:

- Fetches all keys from production CloudflareKV
- Fetches all keys from local CloudflareKV
- Only adds keys that are missing locally (never overwrites)
- Useful for syncing ETL cache data (Spotify playlists, YouTube URLs, etc.)

**Option 3: Direct Production Connection** (Read-only queries)

Create `.env.production` with production credentials:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://user:pass@host:6379
```

Connect via Django shell:

```bash
cd backend
export $(cat ../.env.production | xargs)
python manage.py shell
```

**WARNING**: Always use read-only queries when directly connected to production. Never run `.save()`, `.update()`, `.delete()`, or `.create()` manually.

### Safe Production Queries

**Read-only queries in Django shell**:

```python
from core.models import TrackModel, ServiceTrackModel, PlaylistModel
from core.models.play_counts import HistoricalTrackPlayCountModel
from django.utils import timezone

# Count total tracks
TrackModel.objects.count()

# Check tracks missing YouTube URLs
TrackModel.objects.filter(youtube_url__isnull=True).count()

# Find duplicates by Spotify ID
from django.db.models import Count
TrackModel.objects.values('spotify_id').annotate(
    count=Count('id')
).filter(count__gt=1)

# Check play count data for today
today = timezone.now().date()
HistoricalTrackPlayCountModel.objects.filter(recorded_date=today).count()

# Verify ETL ran successfully
from core.models.genre_service import ServiceModel
for service in ServiceModel.objects.all():
    playlist_count = PlaylistModel.objects.filter(service=service).count()
    track_count = ServiceTrackModel.objects.filter(service=service).count()
    print(f'{service.name}: {playlist_count} playlists, {track_count} tracks')
```

## Data Models

### Core Models

**TrackModel** (`backend/core/models/track.py`)

- Canonical tracks deduplicated across services
- Fields: `track_name`, `artist_name`, `spotify_id`, `youtube_url`, `spotify_image_url`

**ServiceTrackModel** (`backend/core/models/track.py`)

- Service-specific track entries (e.g., same song on Spotify vs Apple Music)
- Links to `TrackModel` (canonical) + `PlaylistModel` + `ServiceModel`

**PlaylistModel** (`backend/core/models/playlist.py`)

- Service playlists (e.g., "RapCaviar" on Spotify)
- Fields: `name`, `service`, `genre`, `description`, `image_url`

**RawPlaylistDataModel** (`backend/core/models/playlist.py`)

- Raw JSON responses from external APIs (Spotify, RapidAPI, SoundCloud)
- Used for debugging API response issues

**HistoricalTrackPlayCountModel** (`backend/core/models/play_counts.py`)

- Daily snapshots of play counts for trending analysis
- Fields: `track`, `service`, `play_count`, `recorded_date`

**AggregateTrackPlayCountModel** (`backend/core/models/play_counts.py`)

- Computed weekly percentage changes
- Fields: `track`, `service`, `play_count`, `weekly_percent_change`, `computed_date`

### Relationships

```
GenreModel (hip-hop, pop, rock)
    └── PlaylistModel (RapCaviar, Today's Top Hits)
            └── ServiceTrackModel (position, trending %)
                    └── TrackModel (canonical track with YouTube URL)
                            └── HistoricalTrackPlayCountModel (daily play counts)
                                    └── AggregateTrackPlayCountModel (weekly trends)
```

## Common Issues & Debugging

### Issue: Missing Tracks in Production

**Symptoms**: Frontend shows fewer tracks than expected, genres missing data

**Debugging Steps**:

```bash
# 1. Sync production to local
make sync-prod

# 2. Check track counts by service
cd backend && python manage.py shell
```

```python
from core.models import ServiceTrackModel, TrackModel
from core.models.genre_service import ServiceModel

for service in ServiceModel.objects.all():
    service_tracks = ServiceTrackModel.objects.filter(service=service).count()
    print(f"{service.name}: {service_tracks} service tracks")

# Check canonical tracks
print(f"Total canonical tracks: {TrackModel.objects.count()}")

# Find tracks missing YouTube URLs
missing_youtube = TrackModel.objects.filter(youtube_url__isnull=True).count()
print(f"Tracks missing YouTube URLs: {missing_youtube}")
```

**Resolution**:

- If data is stale, check GitHub Actions for failed ETL runs
- If YouTube URLs missing, check `GOOGLE_API_KEY` in GitHub Secrets
- If RapidAPI data missing, verify API keys (`X_RAPIDAPI_KEY_A`, `X_RAPIDAPI_KEY_B`, `X_RAPIDAPI_KEY_C`)

### Issue: Play Count Data Missing

**Symptoms**: Trending percentages not showing, weekly changes at 0%

**Debugging Steps**:

```python
from core.models.play_counts import HistoricalTrackPlayCountModel, AggregateTrackPlayCountModel
from django.utils import timezone
from datetime import timedelta

# Check historical data for today
today = timezone.now().date()
today_records = HistoricalTrackPlayCountModel.objects.filter(recorded_date=today)
print(f"Historical play count records for {today}: {today_records.count()}")

# Check 7 days ago (needed for weekly percentage calculation)
seven_days_ago = today - timedelta(days=7)
old_records = HistoricalTrackPlayCountModel.objects.filter(recorded_date=seven_days_ago)
print(f"Historical play count records for {seven_days_ago}: {old_records.count()}")

# Check aggregate data
aggregates = AggregateTrackPlayCountModel.objects.filter(computed_date=today)
print(f"Aggregate play count records: {aggregates.count()}")

# Sample a track to verify weekly change calculation
sample = AggregateTrackPlayCountModel.objects.first()
if sample:
    print(f"Sample: {sample.track.track_name} - {sample.weekly_percent_change}% change")
```

**Resolution**:

- If historical data missing, run `make run-play-count-etl` to backfill
- If 7-day-old data missing, cannot compute weekly changes (need historical data)
- Check GitHub Actions Play Count ETL for API failures

### Issue: Cache Inconsistencies

**Symptoms**: API responses show old data, frontend doesn't reflect latest ETL

**Debugging**:

CloudflareKV cache (used by ETL):

```python
from core.utils.cloudflare_cache import CloudflareCache

cache = CloudflareCache()
# Check specific cache key
value = cache.get("playlist_spotify_37i9dQZF1DX0XUsuxWHRQd")
print(value)
```

Redis cache (used by GraphQL):

```bash
# Clear local Redis cache
make clear-cache

# Or manually clear specific keys
redis-cli -n 1 KEYS "GQL_*"
redis-cli -n 1 DEL "GQL_PLAYLIST:hip-hop:spotify"
```

**Resolution**:

- CloudflareKV cache cleared automatically during Step 2 of Playlist ETL if `--force-refresh` used
- Redis cache cleared and warmed in Step 6 of Playlist ETL (automatic)
- Manual cache clear: `make clear-cache` (Redis only)

### Issue: ETL Takes Too Long

**Symptoms**: GitHub Actions timeout (360 minutes), ETL doesn't complete

**Debugging**:

```bash
# Check logs in GitHub Actions for bottlenecks
# Common issues:
# - Step 2 (Raw Playlist): RapidAPI rate limits, slow Spotify API responses
# - Step 4 (Track Creation): YouTube API quota exceeded
# - SSL timeout errors during long-running API calls
```

**Resolution**:

- Use `--limit 10` flag for testing: `make test-play-count-etl`
- Check API rate limits and quotas
- SSL timeout: ETL automatically closes DB connection between steps (see `connection.close()` in `play_count.py:38,44,50`)

### Issue: Malformed Data (Unicode, Missing Fields)

**Symptoms**: Track names show garbled characters, missing artist names

**Debugging**:

```python
from core.models import TrackModel

# Find tracks with null fields
TrackModel.objects.filter(artist_name__isnull=True).count()
TrackModel.objects.filter(track_name__isnull=True).count()

# Check for unicode issues
for track in TrackModel.objects.filter(track_name__contains='\\x'):
    print(f"Malformed: {track.track_name}")
```

**Resolution**:

- Check raw API responses in `RawPlaylistDataModel`
- Verify API keys are valid and not corrupted
- Run ETL with `--force-refresh` to bypass cached malformed data

## Backfilling & Data Fixes

### Backfill Missing Play Count Data

**Scenario**: Play count ETL failed for several days, need historical data

**Solution**:

```bash
# 1. Sync production to local for safe testing
make sync-prod

# 2. Manually run play count ETL (will create records for today)
cd backend
python manage.py play_count

# 3. If need to backfill specific dates, modify recorded_date in Django shell
python manage.py shell
```

```python
from core.models.play_counts import HistoricalTrackPlayCountModel
from datetime import date

# WARNING: Only do this locally, not in production
# Manually create historical records for missing dates
# (This is a last resort - ETL should run daily)
```

**Best Practice**: Prevent gaps by monitoring GitHub Actions for failures.

### Fix Incorrect Track Data

**Scenario**: Track has wrong YouTube URL, needs correction

**Solution**:

```bash
# 1. Sync production to local
make sync-prod

# 2. Identify incorrect track
cd backend && python manage.py shell
```

```python
from core.models import TrackModel

# Find track
track = TrackModel.objects.get(spotify_id="SPOTIFY_ID_HERE")
print(f"Current YouTube URL: {track.youtube_url}")

# Fix locally to verify
track.youtube_url = "https://www.youtube.com/watch?v=NEW_ID"
track.save()

# Verify fix
track.refresh_from_db()
print(f"Updated YouTube URL: {track.youtube_url}")
```

**To apply fix to production**:

```bash
# Option 1: Let ETL fix it naturally (if API source is corrected)
make run-playlist-etl-force-refresh

# Option 2: Manual production fix (NOT RECOMMENDED)
# Connect to production, run same update, test thoroughly first
```

**Best Practice**: Fix root cause in ETL logic, not manual data patches.

### Delete Duplicate Tracks

**Scenario**: ETL created duplicate tracks with different IDs

**Debugging**:

```python
from django.db.models import Count
from core.models import TrackModel

# Find duplicates by Spotify ID
duplicates = TrackModel.objects.values('spotify_id').annotate(
    count=Count('id')
).filter(count__gt=1)

for dup in duplicates:
    tracks = TrackModel.objects.filter(spotify_id=dup['spotify_id'])
    print(f"Spotify ID {dup['spotify_id']}: {tracks.count()} duplicates")
    for track in tracks:
        print(f"  - ID {track.id}: {track.track_name}")
```

**Resolution**:

```python
# Delete duplicates, keeping the first one
for dup in duplicates:
    tracks = TrackModel.objects.filter(spotify_id=dup['spotify_id']).order_by('id')
    tracks_to_delete = tracks[1:]  # Keep first, delete rest
    for track in tracks_to_delete:
        print(f"Deleting duplicate: {track.id} - {track.track_name}")
        track.delete()
```

**WARNING**: Test locally first with `make sync-prod`, verify ServiceTrackModel references won't break.

## Cache Management

### CloudflareKV Cache (Default/ETL Cache)

**Purpose**: Cache raw API responses (Spotify, RapidAPI, YouTube, SoundCloud)

**Why**: Avoid API rate limits and quota exhaustion

**Stored Data**:

- Spotify playlist JSON responses
- RapidAPI Apple Music playlist data
- SoundCloud playlist HTML/metadata
- YouTube video metadata

**Cache Keys**: Service-specific (e.g., `playlist_spotify_37i9dQZF1DX0XUsuxWHRQd`)

**Clear Cache**: Use `--force-refresh` flag

```bash
make run-playlist-etl-force-refresh
```

**Access via Python**:

```python
from core.utils.cloudflare_cache import CloudflareCache

cache = CloudflareCache()
value = cache.get("cache_key")
cache.set("cache_key", "value", ttl_seconds=3600)
cache.delete("cache_key")
```

### Redis Cloud Cache (GraphQL Cache)

**Purpose**: Cache GraphQL query responses for fast frontend API responses

**Why**: Serverless functions don't cache across invocations, Redis persists cache

**Stored Data**:

- `GQL_PLAYLIST` - Track listings by genre/service
- `GQL_PLAY_COUNT` - Play count trending data
- `GQL_PLAYLIST_METADATA` - Playlist metadata for header

**Cache Keys**: GraphQL query-specific (e.g., `GQL_PLAYLIST:hip-hop:spotify`)

**Clear Cache**:

```bash
make clear-cache    # Clears local Redis cache
```

**Production Cache Warming**: Automatic during Step 6 of Playlist ETL (`clear_and_warm_cache.py`)

**Performance**: <200ms API responses with warmed cache vs 10+ seconds without

## Manual ETL Operations

### Run Playlist ETL Locally

```bash
# Start local backend and Redis
make serve-backend

# Run full playlist ETL
cd backend
python manage.py playlist_etl

# Run with force refresh (bypass CloudflareKV cache)
python manage.py playlist_etl --force-refresh
```

### Run Play Count ETL Locally

```bash
# Run full play count ETL
cd backend
python manage.py play_count

# Test with 10 tracks only
python manage.py play_count --limit 10
```

### Manually Trigger GitHub Actions ETL

1. Go to [GitHub Actions](https://github.com/EliJaghab/tunemeld/actions)
2. Select "Playlist ETL" or "Historical Track Play Count ETL"
3. Click "Run workflow"
4. Choose options:
   - **Playlist ETL**: `force_refresh` (bypass API cache), `clear_gql_cache` (clear Redis)
   - **Play Count ETL**: `clear_play_count_cache` (clear Redis play count cache)

### Debug Failed GitHub Actions Run

**Steps**:

1. Navigate to failed workflow run
2. Check "Run Playlist ETL Pipeline" or "Run Historical Track Play Count ETL" step
3. Look for error messages:
   - `RapidAPI rate limit exceeded` → Wait 24 hours or use different API key
   - `YouTube API quota exceeded` → Wait for quota reset (resets daily)
   - `SSL connection has been closed unexpectedly` → DB timeout (ETL auto-retries)
4. Check "Verify ETL pipeline results" step for data counts
5. If ETL succeeded but data missing, check cache warming step

**Common Fixes**:

- Rotate RapidAPI keys in GitHub Secrets (`X_RAPIDAPI_KEY_A`, `X_RAPIDAPI_KEY_B`, `X_RAPIDAPI_KEY_C`)
- Increase `timeout-minutes` in workflow YAML if ETL legitimately takes longer
- Run `make test-play-count-etl` locally to isolate issue

## Verification Queries

### Check ETL Data Completeness

**Django Shell**:

```python
from core.models import RawPlaylistDataModel, TrackModel, ServiceTrackModel, PlaylistModel
from core.models.genre_service import GenreModel, ServiceModel

# Summary stats
print(f'Raw playlist records: {RawPlaylistDataModel.objects.count()}')
print(f'Unique tracks: {TrackModel.objects.count()}')
print(f'Service track entries: {ServiceTrackModel.objects.count()}')
print(f'Service playlists: {PlaylistModel.objects.count()}')
print(f'Genres: {GenreModel.objects.count()}')
print(f'Services: {ServiceModel.objects.count()}')

# Breakdown by service
for service in ServiceModel.objects.all():
    playlist_count = PlaylistModel.objects.filter(service=service).count()
    track_count = ServiceTrackModel.objects.filter(service=service).count()
    print(f'{service.name}: {playlist_count} playlists, {track_count} tracks')
```

### Verify Play Count Trending Data

```python
from core.models.play_counts import HistoricalTrackPlayCountModel, AggregateTrackPlayCountModel
from django.utils import timezone

today = timezone.now().date()

# Historical data
historical_count = HistoricalTrackPlayCountModel.objects.filter(recorded_date=today).count()
print(f'Historical play count records for {today}: {historical_count}')

# Aggregate data
aggregate_count = AggregateTrackPlayCountModel.objects.filter(computed_date=today).count()
print(f'Aggregate play count records: {aggregate_count}')

# Sample trending data
top_tracks = AggregateTrackPlayCountModel.objects.filter(
    computed_date=today
).order_by('-weekly_percent_change')[:10]

print("\nTop 10 trending tracks:")
for track in top_tracks:
    print(f"{track.track.track_name} by {track.track.artist_name}: +{track.weekly_percent_change}%")
```

### Check Cache Warming Success

**Redis Cache**:

```bash
redis-cli -n 1 KEYS "GQL_*"
redis-cli -n 1 GET "GQL_PLAYLIST:hip-hop:spotify"
```

**Expected Keys**:

- `GQL_PLAYLIST:hip-hop:spotify`
- `GQL_PLAYLIST:hip-hop:apple_music`
- `GQL_PLAYLIST:hip-hop:youtube`
- `GQL_PLAYLIST:hip-hop:soundcloud`
- `GQL_PLAY_COUNT:hip-hop:spotify`
- `GQL_PLAY_COUNT:hip-hop:youtube`
- `GQL_PLAYLIST_METADATA:hip-hop:spotify`
- (Repeat for each genre: pop, rock, country, etc.)

**If keys missing**: Run `cd backend && python manage.py clear_and_warm_cache`

## Safety Guidelines

### Production Data Operations

1. **NEVER run destructive operations directly in production**

   - No manual `.delete()`, `.update()`, `.create()` in production shell
   - Always test locally with `make sync-prod` first

2. **Always use read-only queries when connected to production**

   - Use `.count()`, `.filter()`, `.values()` for analysis
   - Export data to JSON if needed: `python manage.py dumpdata core.TrackModel > tracks.json`

3. **Let ETL fix data issues, not manual patches**

   - Fix root cause in ETL code, redeploy, let ETL run
   - Manual fixes are temporary band-aids, not solutions

4. **Test migrations locally before production**

   - Run `make makemigrations` locally
   - Apply with `make migrate-dev` (SQLite)
   - Test with `make sync-prod` to verify against production data
   - Let GitHub Actions apply migrations to production (automatic)

5. **Monitor GitHub Actions for ETL failures**

   - Set up notifications for workflow failures
   - Check logs immediately when ETL fails
   - Backfill data ASAP to avoid trending data gaps

6. **Use `--limit` flag for testing ETL changes**

   - `python manage.py play_count --limit 10` for quick iteration
   - Test locally before deploying to GitHub Actions

7. **Rotate API keys if rate limits hit**
   - RapidAPI has 3 keys (`X_RAPIDAPI_KEY_A`, `X_RAPIDAPI_KEY_B`, `X_RAPIDAPI_KEY_C`)
   - Rotate in GitHub Secrets, redeploy ETL
   - Consider upgrading API plan if consistently hitting limits

## Troubleshooting Workflows

### Workflow 1: Frontend Shows No Tracks

**Steps**:

1. Check production API response:
   ```bash
   curl https://tunemeld.com/api/graphql \
     -H "Content-Type: application/json" \
     -d '{"query":"{ tracks(genre: \"hip-hop\", service: \"spotify\") { trackName artistName } }"}'
   ```
2. If API returns empty, check database:
   ```bash
   make sync-prod
   cd backend && python manage.py shell
   ```
   ```python
   from core.models import ServiceTrackModel
   ServiceTrackModel.objects.filter(
       playlist__genre__name='hip-hop',
       service__name='spotify'
   ).count()
   ```
3. If count is 0, ETL failed. Check GitHub Actions logs.
4. If count is >0, cache issue. Clear Redis:
   ```bash
   make clear-cache
   cd backend && python manage.py clear_and_warm_cache
   ```

### Workflow 2: Trending Percentages All Zero

**Steps**:

1. Check if play count ETL ran today:

   ```python
   from core.models.play_counts import HistoricalTrackPlayCountModel
   from django.utils import timezone

   today = timezone.now().date()
   today_count = HistoricalTrackPlayCountModel.objects.filter(recorded_date=today).count()
   print(f"Records for {today}: {today_count}")
   ```

2. If count is 0, ETL didn't run. Check GitHub Actions.
3. If count >0, check 7 days ago:

   ```python
   from datetime import timedelta

   seven_days_ago = today - timedelta(days=7)
   old_count = HistoricalTrackPlayCountModel.objects.filter(recorded_date=seven_days_ago).count()
   print(f"Records for {seven_days_ago}: {old_count}")
   ```

4. If old count is 0, weekly change can't be computed. Backfill historical data.
5. If both counts >0, check aggregate computation:

   ```python
   from core.models.play_counts import AggregateTrackPlayCountModel

   agg_count = AggregateTrackPlayCountModel.objects.filter(computed_date=today).count()
   print(f"Aggregate records: {agg_count}")
   ```

6. If aggregate count is 0, run `python manage.py play_count` to recompute.

### Workflow 3: Duplicate Tracks in Database

**Steps**:

1. Identify duplicates:

   ```python
   from django.db.models import Count
   from core.models import TrackModel

   duplicates = TrackModel.objects.values('spotify_id').annotate(
       count=Count('id')
   ).filter(count__gt=1)
   ```

2. Review duplicate creation logic in ETL (`playlist_etl_modules/c_track.py`)
3. Fix ETL logic to prevent future duplicates
4. Backfill production:
   ```bash
   make run-playlist-etl-force-refresh
   ```
5. Manually clean up existing duplicates (test locally first):
   ```python
   for dup in duplicates:
       tracks = TrackModel.objects.filter(spotify_id=dup['spotify_id']).order_by('id')
       tracks_to_delete = tracks[1:]
       for track in tracks_to_delete:
           track.delete()
   ```

## Environment Variables

### Required for ETL

**Database**:

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis Cloud connection string

**APIs**:

- `X_RAPIDAPI_KEY_A`, `X_RAPIDAPI_KEY_B`, `X_RAPIDAPI_KEY_C` - RapidAPI keys (Apple Music, SoundCloud)
- `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET` - Spotify API credentials
- `GOOGLE_API_KEY` - YouTube Data API key

**Cloudflare**:

- `CF_ACCOUNT_ID` - Cloudflare account ID
- `CF_NAMESPACE_ID` - CloudflareKV namespace ID
- `CF_API_TOKEN` - Cloudflare API token

**Django**:

- `DJANGO_SECRET_KEY` - Django secret key

### Local Development

**Required files**:

- `.env.dev` - Local development environment (SQLite, local Redis)
- `.env.production` - Production credentials (PostgreSQL, Redis Cloud)

**Example `.env.dev`**:

```bash
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/1
DJANGO_SECRET_KEY=local-dev-secret-key-not-for-production
# API keys same as production
X_RAPIDAPI_KEY_A=...
SPOTIFY_CLIENT_ID=...
GOOGLE_API_KEY=...
CF_ACCOUNT_ID=...
CF_NAMESPACE_ID=...
CF_API_TOKEN=...
```

## GitHub Actions Workflow Details

### Playlist ETL Workflow

**File**: `.github/workflows/playlist_etl.yml`
**Trigger**: Daily at 2:30 AM UTC, manual dispatch, push to ETL code
**Timeout**: 360 minutes (6 hours)
**Manual Options**:

- `force_refresh` - Bypass CloudflareKV cache, pull fresh API data
- `clear_gql_cache` - Clear Redis GraphQL cache before warming

**Workflow Steps**:

1. Pre-migration database safety check
2. Apply database migrations to production PostgreSQL
3. Run Playlist ETL Pipeline
4. Verify ETL pipeline results (data counts)
5. Post-ETL database validation

### Play Count ETL Workflow

**File**: `.github/workflows/play_count.yml`
**Trigger**: Daily at 2:00 AM UTC, manual dispatch
**Timeout**: 360 minutes (6 hours)
**Manual Options**:

- `clear_play_count_cache` - Clear Redis play count cache before warming

**Workflow Steps**:

1. Pre-migration database safety check
2. Apply database migrations to production PostgreSQL
3. Run Historical Track Play Count ETL
4. Verify ETL pipeline results (play count data counts)
5. Post-ETL database validation

### Cache Warming Workflow

**File**: `.github/workflows/clear-and-warm-cache.yml`
**Purpose**: Manually clear and warm Redis cache without running full ETL
**Use Case**: Cache corruption, need to refresh GraphQL responses without re-scraping data

## Contact & Resources

**GitHub Actions**: https://github.com/EliJaghab/tunemeld/actions
**Vercel Dashboard**: https://vercel.com/dashboard
**Redis Cloud Console**: https://app.redislabs.com/
**Cloudflare Dashboard**: https://dash.cloudflare.com/

**Useful Commands Quick Reference**:

```bash
make sync-prod                # Sync production data to local
make run-playlist-etl         # Run playlist ETL locally
make run-play-count-etl       # Run play count ETL locally
make test-play-count-etl      # Test play count ETL with 10 tracks
make clear-cache              # Clear local Redis cache
make serve-backend            # Start local backend + Redis
cd backend && python manage.py shell  # Django shell for queries
```
