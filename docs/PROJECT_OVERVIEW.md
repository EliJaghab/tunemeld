# TuneMeld Project Overview

## What is TuneMeld?

TuneMeld is a music analytics platform that aggregates playlist data from multiple streaming services (Spotify, SoundCloud, Apple Music) to create unified, cross-platform music rankings. The platform tracks view counts, generates analytics, and provides insights into music trends across different genres.

## Current Architecture

### System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend APIs   │    │   Data Layer    │
│   (Static Web)  │◄──►│  (Django + CF)   │◄──►│   (MongoDB)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌────────▼────────┐              │
         │              │  ETL Pipeline   │              │
         └──────────────►│  (Python)      │◄─────────────┘
                        └─────────────────┘
```

### 1. Frontend (`/docs/`)

- **Technology**: Vanilla JavaScript, HTML, CSS
- **Current State**: Static website hosted on GitHub Pages
- **Features**:
  - Genre-based playlist viewing
  - Interactive charts and visualizations
  - Dark/light mode toggle
  - Service-specific playlist displays

### 2. ETL Pipeline (`/playlist_etl/`)

- **Technology**: Python with Pydantic models
- **Current State**: Fully functional data processing pipeline
- **Key Components**:
  - `extract.py` - Data extraction from streaming services
  - `transform2.py` - Data normalization and enrichment
  - `aggregate2.py` - Cross-service track matching using ISRC
  - `view_count2.py` - Analytics and view count tracking
  - `models.py` - Type-safe data models

### 3. Django Backend (`/django_backend/`)

- **Technology**: Django REST Framework
- **Current State**: Implemented but not fully deployed
- **API Endpoints**:
  - `/graph-data/<genre>` - Chart visualization data
  - `/playlist-data/<genre>` - Complete playlist information
  - `/service-playlist/<genre>/<service>` - Service-specific playlists
  - `/last-updated/<genre>` - Data freshness timestamps
  - `/header-art/<genre>` - Playlist artwork and metadata

### 4. Data Layer (MongoDB)

- **Technology**: MongoDB with multiple collections
- **Current State**: Operational with normalized schema
- **Collections**:
  - `raw_playlists` - Original scraped data
  - `track_playlist` - Aggregated rankings
  - `track` - Individual track metadata
  - `view_counts_playlists` - Analytics data
  - Various cache collections

## Data Flow

### Current Process

1. **Extraction**: ETL pipeline scrapes playlists from Spotify, SoundCloud, Apple Music
2. **Transformation**: Raw data is normalized, ISRCs are resolved, YouTube URLs are matched
3. **Aggregation**: Tracks are ranked across services using ISRC matching
4. **Storage**: Processed data is stored in MongoDB collections
5. **Analytics**: View counts are tracked and historical data is maintained
6. **Serving**: Frontend currently reads from static files, Django backend provides API access

### Key Features

#### Cross-Service Track Matching

- Uses ISRC (International Standard Recording Code) for accurate track identification
- Prioritizes services in order: Apple Music → SoundCloud → Spotify
- Handles missing ISRCs gracefully with fallback matching

#### View Count Analytics

- Tracks play counts from Spotify and YouTube over time
- Calculates delta changes and growth trends
- Stores historical view data for trend analysis

#### Caching Strategy

- MongoDB collections for persistent caching (ISRCs, YouTube URLs, album covers)
- Cloudflare KV for API response caching
- Smart cache invalidation and warming

## Technology Stack

### Backend

- **Python 3.10+** - ETL pipeline and data processing
- **Django 3.x** - REST API framework
- **Pydantic** - Data validation and serialization
- **PyMongo** - MongoDB integration
- **Selenium WebDriver** - Web scraping for view counts

### Frontend

- **Vanilla JavaScript** - Client-side logic
- **Chart.js** - Data visualization
- **CSS Grid/Flexbox** - Responsive layouts
- **Progressive Web App** features

### Infrastructure

- **MongoDB Atlas** - Database hosting
- **Cloudflare** - CDN and KV storage
- **Railway/Heroku** - Backend deployment (planned)
- **GitHub Pages** - Frontend hosting

## Current Status

### ✅ Working Components

- ETL pipeline with full data processing
- MongoDB schema and data storage
- Frontend user interface
- Basic Django API structure

### ⚠️ Partially Complete

- Django backend API (implemented but not deployed)
- Data consistency between old and new APIs
- Frontend integration with backend APIs

### ❌ Pending Work

- Backend deployment to production
- Frontend migration from static files to API calls
- Complete view count integration
- Error handling and monitoring

## Key Challenges Addressed

### 1. Wide Document Problem

**Issue**: Original MongoDB documents were too wide, causing performance issues
**Solution**: Normalized schema with separate collections for different data types

### 2. Cross-Service Data Matching

**Issue**: Same tracks appear differently across services
**Solution**: ISRC-based matching with intelligent fallback strategies

### 3. Real-Time Analytics

**Issue**: Need for up-to-date view counts and trend data
**Solution**: Separate analytics pipeline with historical data tracking

### 4. Scalable Architecture

**Issue**: Moving from static files to proper backend architecture
**Solution**: Django REST API with MongoDB and Cloudflare caching

## Next Phase Goals

1. **Complete Backend Migration**: Deploy Django API to production
2. **Data Consistency**: Resolve API response differences
3. **Frontend Integration**: Switch to backend API calls
4. **Performance Optimization**: Implement efficient caching and querying
5. **Monitoring & Observability**: Add comprehensive logging and metrics

## File Structure

```
tunemeld/
├── docs/                    # Frontend static files
├── playlist_etl/           # ETL pipeline
├── django_backend/         # REST API backend
├── backend/               # Cloudflare Workers (legacy)
├── output_static/         # Generated static files
└── staticfiles/          # Django static files
```

This project represents a sophisticated transition from a document-based architecture to a more scalable, relational approach while maintaining the rich analytics and cross-platform integration that makes TuneMeld unique.
