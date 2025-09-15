# TuneMeld 🎵

## Why TuneMeld?

I built TuneMeld because I found myself constantly checking different streaming services to see what they thought were the top tracks each week. This manual process was time-consuming and inefficient.

**TuneMeld solves this by aggregating playlist data from major streaming services to show where they agree on top tracks** - essentially saving time by finding the tracks that matter across all platforms.

<img width="894" alt="Screenshot 2024-08-07 at 9 37 06 PM" src="https://github.com/user-attachments/assets/618ab389-cbae-4e77-ab29-3256e2422e1e">

## Architecture Overview

TuneMeld is a data pipeline and web application that aggregates music playlist data from multiple streaming services.

**Tech Stack:**

- **Backend**: Django + PostgreSQL on Railway
- **Frontend**: Static HTML/JS served via GitHub Pages
- **API**: GraphQL for efficient data fetching
- **CDN**: Cloudflare for global distribution
- **Data Sources**: Spotify (SpotDL), Apple Music & SoundCloud (RapidAPI)

## How It Works

### 1. Data Sources & Configuration

Playlists are defined in `django_backend/core/utils/constants.py`:

- **Services**: Spotify, Apple Music, SoundCloud
- **Genres**: Dance/Electronic, Hip-Hop/Rap, Country, Pop
- **Playlists**: Editorial/curated playlists from each service

**Why these choices?** These are the most popular platforms with human-curated editorial playlists that reflect current music trends.

### 2. Data Pipeline

#### Playlist ETL Pipeline

**Schedule**: Daily at 2:30 AM UTC (`30 2 * * *`) via GitHub Actions

**9-Step Process:**

1. **Setup** - Initialize genres and services in database
2. **Cache Check** - Clear stale RapidAPI/Spotify caches during scheduled window
3. **Extract** - Fetch playlist data (cache-first to avoid redundant API calls):
   - Apple Music & SoundCloud via RapidAPI
   - Spotify via SpotDL
4. **Transform** - Create service-specific track records
5. **Canonicalize** - Generate unified tracks via ISRC normalization + YouTube URL lookup
6. **Aggregate** - Rank tracks by cross-service agreement
7. **Cache Clear** - Reset GraphQL cache for fresh data
8. **Cache Warm** - Pre-populate GraphQL cache with common queries
9. **Deploy** - Blue-green deployment (remove previous ETL data)

**ISRC Normalization**: Groups tracks by ISRC code to solve "same song, different metadata" problem. Spotify/SoundCloud provide ISRC directly; Apple Music tracks require Spotify API lookup (`get_spotify_isrc`). Priority: Spotify > Apple Music > SoundCloud.

**Cache Strategy**: ETL checks Django cache first (RapidAPI: 7 days, Spotify: 7 days, YouTube: permanent, ISRC: permanent) to minimize API costs by 95%.

#### View Count ETL Pipeline

**Schedule**: Daily at 2:00 AM UTC (`0 2 * * *`) via GitHub Actions

**Process**: Updates Spotify and YouTube view counts for existing tracks using web scraping with retry logic and comprehensive failure tracking.

**Why Daily**: Playlists update weekly, but view counts change daily for engagement tracking.

### 3. Data Storage

PostgreSQL models track the data lifecycle:

```
RawPlaylistData → ServiceTrack → Track → Aggregated Rankings
```

Each ETL run is tracked with a UUID for versioning and rollback capability.

**Why PostgreSQL?** Relational data structure, ACID compliance, excellent Railway support, complex query capabilities for ranking algorithms.

### 4. API Layer

GraphQL schema provides efficient data access:

- Query types: Genre, Playlist, Track, Service
- Single endpoint for all data needs
- Automatic query optimization

**Why GraphQL?** Frontend can request exactly what it needs, reducing bandwidth and improving performance. Single endpoint simplifies CORS and caching.

### 5. Deployment Architecture

#### ETL Pipeline Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   GitHub    │────▶│   Railway    │────▶│ PostgreSQL  │
│   Actions   │     │   (Django)   │     │  (Railway)  │
│   (ETL)     │     │  (Backend)   │     │ (Database)  │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ Django Cache │
                    │   (Redis)    │
                    │ • RapidAPI   │
                    │ • Spotify    │
                    │ • YouTube    │
                    │ • ISRC       │
                    └──────────────┘
```

**Data Processing Flow:**

- GitHub Actions runs ETL scripts daily (playlist ETL, view count ETL)
- ETL checks Django cache first to avoid redundant API calls
- Only fetches from external APIs (RapidAPI, Spotify, YouTube) if data not cached
- Scripts connect to Railway's Django app to access the database
- Data gets processed and stored in Railway's PostgreSQL

#### Web Application Architecture

```
┌──────────────┐    ┌──────────────┐     ┌─────────────┐
│ GitHub Pages │    │   Railway    │────▶│ PostgreSQL  │
│  (Frontend)  │───▶│   (Django)   │     │ (Database)  │
│  Static HTML │    │   GraphQL    │     │             │
└──────────────┘    └──────────────┘     └─────────────┘
        │                    │
        ▼                    ▼
┌──────────────┐    ┌──────────────┐
│   Browser    │    │ Cloudflare   │
│              │◀───│     CDN      │
└──────────────┘    └──────────────┘
```

**User-Facing Flow:**

- Static frontend (GitHub Pages) makes GraphQL requests to Railway Django
- Railway Django serves the GraphQL API and queries PostgreSQL
- Cloudflare CDN caches responses globally

**Backend**: Django on Railway - managed infrastructure, automatic scaling, integrated PostgreSQL
**Frontend**: `/docs` folder served via GitHub Pages at tunemeld.com

**Why split architecture?**

- Cost efficiency (GitHub Pages is free)
- Independent scaling of frontend/backend
- CDN benefits for static assets
- Simplified deployment pipeline

### 6. Frontend

Static HTML/CSS/JavaScript in `/docs` directory:

- No framework overhead for fast loading
- GraphQL client for data fetching
- Service-specific playlist views with logos

**Why static?** The app is read-heavy with weekly updates. Static sites are incredibly fast, SEO-friendly, and cost-effective to serve globally.

## Running Locally

### Prerequisites

- Python 3.13+
- PostgreSQL
- Make

### Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and configure
3. Install dependencies: `make install`
4. Run migrations: `make migrate`

### Development

```bash
# Start servers
make serve-frontend  # http://localhost:8080
make serve-backend   # http://localhost:8000

# Run ETL pipeline
python manage.py a_playlist_etl

# Format code (required before committing)
make format
```

## Deployment

### Backend (Railway)

- Automatic deploys from main branch
- Environment variables in Railway dashboard
- PostgreSQL provisioned automatically

### Frontend (GitHub Pages)

- Automatic deployment when `/docs` changes
- Custom domain via CNAME file
- Cloudflare CDN for performance

## Key Design Principles

1. **Data Quality Over Quantity**: Focus on editorial playlists that represent human curation
2. **Performance First**: Multi-layer caching, static frontend, CDN distribution
3. **Cost Efficiency**: Leverage free tiers (GitHub Pages, Railway starter, Cloudflare)
4. **Maintainability**: Clear separation of concerns, comprehensive logging, blue-green deployments
5. **User Experience**: Show consensus across services, fast loading, mobile-friendly

## Tech Stack Rationale

- **Django**: Mature, batteries-included, excellent ORM for complex queries
- **PostgreSQL**: Best open-source relational database, Railway integration
- **GraphQL**: Efficient data fetching, single endpoint, future-proof API
- **Railway**: Zero-config deployments, integrated PostgreSQL, great DX
- **GitHub Pages**: Free, reliable, perfect for static content
- **Cloudflare**: Free CDN, DDoS protection, analytics

## License

MIT
