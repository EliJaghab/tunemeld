# TuneMeld

_Discover top tracks by streaming service consensus_

## Table of Contents

- [Why TuneMeld?](#why-tunemeld)
- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Data Pipeline](#data-pipeline)
- [Data Sources](#data-sources)
- [Cache Strategy](#cache-strategy)
- [Deployment](#deployment)
- [Development](#development)
- [Performance](#performance)
- [API Documentation](#api-documentation)

## Why TuneMeld?

TuneMeld aggregates playlist data from major streaming services to show where they agree on top tracks - saving you time by finding the tracks that matter across all platforms.

Instead of manually checking Spotify, Apple Music, and SoundCloud each week, TuneMeld shows you the consensus picks automatically.

## Architecture Overview

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Frontend   │───▶│   Backend   │───▶│ PostgreSQL  │
│ Static HTML │    │   Django    │    │  Database   │
│ Cloudflare  │    │   Vercel    │    │   Vercel    │
│   Pages     │    │ Serverless  │    │  Postgres   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                    │
       ▼                    ▼
┌─────────────┐    ┌─────────────┐
│  Browser    │    │ Vercel Redis│
│   Client    │    │ + Cloudflare│
│             │    │     KV      │
└─────────────┘    └─────────────┘
```

## Tech Stack

### Frontend

- **TypeScript** - Type-safe static site generation
- **Cloudflare Pages** - Global CDN distribution
- **GraphQL Client** - Efficient data fetching

### Backend

- **Django** - Serverless functions on Vercel
- **GraphQL API** - Single endpoint for all data
- **PostgreSQL** - Vercel Postgres (managed database)

### Caching

- **Vercel Redis** - Managed Redis instance for GraphQL query results
- **CloudflareKV** - ETL/API data (RapidAPI, Spotify, YouTube responses)

### Data Sources

- **Spotify** - Via SpotDL (ISRC + metadata)
- **Apple Music** - Via RapidAPI
- **SoundCloud** - Via RapidAPI
- **YouTube** - View count scraping

## Data Pipeline

### Playlist ETL Pipeline

**Schedule**: Weekly on Saturday at 2:30 AM UTC via GitHub Actions

**Why This Schedule**: New music releases Friday at midnight globally. Streaming services update their editorial playlists Friday/Saturday. Running ETL on Saturday afternoon Eastern time (2:30 AM UTC Sunday) captures all fresh playlist updates after the weekly music release cycle.

**9-Step Process**:

1. **Setup** - Initialize database with genres/services
2. **Cache Check** - Clear stale external API caches
3. **Extract** - Fetch playlist data (cache-first to minimize API costs)
4. **Transform** - Create service-specific track records
5. **Canonicalize** - Unify tracks via ISRC normalization + YouTube lookup
6. **Aggregate** - Rank tracks by cross-service consensus
7. **Cache Clear** - Reset GraphQL cache
8. **Cache Warm** - Pre-populate Redis with common GraphQL queries (serverless optimization)
9. **Deploy** - Blue-green deployment

### View Count ETL Pipeline

**Schedule**: Daily at 2:00 AM UTC via GitHub Actions

Updates Spotify and YouTube view counts for engagement tracking.

## Data Sources

TuneMeld tracks trending music by aggregating playlists that are manually curated by editorial teams at Spotify, Apple Music, and SoundCloud. Each service has professional curators who hand-pick tracks after new music releases every Friday, updating their playlists weekly. TuneMeld aggregates these expert-selected tracks across all three platforms to find cross-service consensus, resulting in 12 distinct data sources (3 services × 4 genres).

### Services & Data Collection Methods

**Spotify**

- Method: SpotDL library for playlist extraction
- Provides: Track metadata, ISRCs, Spotify URLs
- Playlist Type: Editorial curator playlists (manually curated by Spotify's editorial team)

**Apple Music**

- Method: RapidAPI (Apple Music API)
- Provides: Track metadata, ISRCs, Apple Music URLs
- Playlist Type: Editorial curator playlists (manually curated by Apple Music's editorial team)

**SoundCloud**

- Method: RapidAPI (SoundCloud API)
- Provides: Track metadata, SoundCloud URLs
- Playlist Type: Curator playlists and trending charts (manually curated by SoundCloud's editorial team)

### Genres Tracked

- Pop
- Dance/Electronic
- Hip-Hop/Rap
- Country

### Update Schedule

**When**: Every Saturday at 2:30 AM UTC (Saturday afternoon Eastern Time)

**Why This Schedule**: New music releases Friday at midnight globally. Each streaming service's curators manually update their editorial playlists every Friday/Saturday, hand-picking the best new releases across genres. Running ETL on Saturday captures all fresh curator selections from the weekly music release cycle.

**Frequency**: Weekly (aligned with music industry release schedule)

**Volume**: ~220-250 unique curator-selected tracks per week across all playlists

### Data Collection Workflow

1. **Playlist Extraction**: Fetch manually curated playlists from all 12 sources (3 services × 4 genres)
2. **ISRC Lookup**: Query Spotify API to extract ISRCs for cross-platform track matching
3. **Metadata Enrichment**: Gather YouTube view counts, album covers, and platform URLs
4. **Normalization**: Deduplicate tracks using ISRCs (same song across different platforms)
5. **Ranking**: Calculate aggregate scores based on cross-service curator consensus

### ISRC Normalization

Groups tracks by International Standard Recording Code (ISRC) to solve "same song, different metadata" problem. When a track appears on multiple platforms, TuneMeld unifies them into a single canonical record.

**Priority**: Spotify > Apple Music > SoundCloud (metadata quality)

**Configuration**: `backend/core/constants.py` - Contains genre definitions, playlist URLs, and service configurations

## Cache Strategy

### Two-Tier Architecture

**Why Two-Tier Caching?**

**Fast User Cache** (Vercel Redis): Stores final GraphQL results that users request. Fast access, frequently accessed data.

**Cost-Effective ETL Cache** (CloudflareKV): Stores expensive external API responses (RapidAPI, Spotify). Prevents hitting API rate limits and reduces costs by 95%.

**Design Decision**: Separate caches optimize for different access patterns - user-facing speed vs ETL cost efficiency.

**Serverless Optimization**: Redis cache is populated by ETL pipeline only (not on serverless startup) to avoid function cold-start delays while maintaining persistent cache across invocations.

## Deployment

### Frontend: Cloudflare Pages

- Static files served globally
- Auto-deployment from `frontend/` directory changes
- Build: `cd frontend && npm ci && npm run build`
- Output: `frontend/dist/`

### Backend: Vercel Serverless

- Django functions auto-deployed from Git
- Environment variables in Vercel dashboard
- PostgreSQL connection via Neon

### Database: Vercel Postgres

- Managed PostgreSQL with autoscaling
- Branching for preview deployments

## Development

### Prerequisites

- Python 3.12+ (Vercel serverless compatibility)
- Node.js + TypeScript (frontend build)
- Redis (local development cache)

### Setup

```bash
# Start servers (use Makefile only)
make serve-frontend    # http://localhost:8080
make serve-backend     # http://localhost:8000

# Run ETL pipeline
make run-playlist-etl  # Full ETL
make test-playlist-etl # Limited test run

# Format code (required before commits)
make format
```

### Local Architecture

- **Frontend**: TypeScript compiled to static files, served by Django in dev
- **Backend**: Django development server with GraphQL
- **Images**: Symlinks from `backend/static/images/` → `frontend/images/`
- **Cache**: Local Redis instance for development
- **Database**: Connects to Neon PostgreSQL (shared dev/prod)

## Performance

### Frontend Latency Issues

**Root Cause**: Cold cache in Vercel serverless environment

**When cache is cold**:

- First request triggers 100+ database queries (2 per track)
- Playlist with 50 tracks = 100 database round-trips
- Response time: 5-10 seconds

**When cache is warm**:

- Single Redis query
- Response time: <100ms

### Performance Analysis

**Current Performance**: API responses consistently achieve 107-193ms response times, well below the <200ms target.

**Architecture Decision**: Startup cache warming is disabled in serverless environment. Instead, Redis cache is populated by the daily ETL pipeline (Step 6: cache warming). Since Redis is persistent across serverless function invocations, this eliminates the overhead of warming cache on every function startup while maintaining fast response times.

**Why This Works**: Vercel Redis is persistent and survives across serverless invocations, so cache populated by ETL pipeline remains available for all subsequent API requests until the next ETL run refreshes it.

## API Documentation

### GraphQL Endpoint

- **URL**: `https://api.tunemeld.com/graphql/`
- **Queries**: Playlist, Track, Genre, Service
- **Cache**: Vercel Redis (7 day TTL)

### GraphQL Schema

- **Queries**: `playlist`, `track`, `genres`, `services`
- **Types**: `PlaylistType`, `TrackType`, `GenreType`, `ServiceType`
- **Arguments**: `genre`, `service`, `isrc`

### Cache Keys

All GraphQL responses cached with structured keys for efficient invalidation and warming.

---

**Built with performance and data quality in mind** 🎵
