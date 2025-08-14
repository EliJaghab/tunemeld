# Staging Environment Setup

## Quick Start (5 minutes)

### 1. **Setup Staging Environment**

```bash
# Copy staging environment file
cp .env.staging .env

# Setup staging database and run full ETL pipeline
cd django_backend
python manage.py setup_staging
```

### 2. **Run End-to-End Test**

```bash
# Test the complete pipeline with validation
python manage.py test_staging_e2e --verbose
```

## What This Gives You

### ✅ **Complete Staging Environment**

- **SQLite Database**: No external database required
- **Sample Data**: Realistic JSON from all 3 services (Spotify, Apple Music, SoundCloud)
- **No External APIs**: Uses fixtures instead of RapidAPI calls
- **Full ETL Pipeline**: Tests all phases (extract → normalize → hydrate)

### ✅ **Sample Data Included**

- **3 Services**: Spotify, Apple Music, SoundCloud
- **2 Genres**: Pop, Hip-Hop
- **Realistic JSON**: Actual API response structures
- **ISRC Testing**: Includes tracks with same ISRC for deduplication testing

### ✅ **End-to-End Validation**

- **Data Integrity**: Validates each ETL stage
- **ISRC Deduplication**: Tests track merging logic
- **Service Preservation**: Ensures service-specific data is maintained
- **Error Handling**: Tests edge cases and failures

## Commands Available

```bash
# Setup staging with sample data
python manage.py setup_staging

# Setup without running ETL (just load fixtures)
python manage.py setup_staging --skip-etl

# Run end-to-end test with detailed output
python manage.py test_staging_e2e --verbose

# Run individual ETL stages on staging data
python manage.py c_normalize_raw_playlists
python manage.py d_hydrate_tracks
```

## Benefits

### 🚀 **Fast Development**

- No API rate limits or costs
- Instant setup and testing
- Consistent, reproducible data

### 🧪 **Comprehensive Testing**

- Tests real JSON structures
- Validates full pipeline
- Catches integration issues

### 🔒 **Safe Environment**

- No production data risk
- No external dependencies
- Works offline

## Staging vs Production

| Feature     | Staging  | Production     |
| ----------- | -------- | -------------- |
| Database    | SQLite   | PostgreSQL     |
| API Calls   | Fixtures | RapidAPI       |
| Spotify     | Mocked   | Real API       |
| Data Volume | Sample   | Full playlists |
| Speed       | Instant  | Minutes        |
| Cost        | Free     | API costs      |

## Next Steps

1. **Validate Your Changes**: Run `python manage.py test_staging_e2e` after any code changes
2. **Add More Sample Data**: Edit `core/fixtures/staging_data.json` to add more test cases
3. **Deploy to Railway**: Use Railway staging environment for cloud testing
4. **CI/CD Integration**: Add staging tests to GitHub workflows
