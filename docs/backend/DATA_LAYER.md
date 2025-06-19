# TuneMeld Data Layer Documentation

## Database Architecture Overview

TuneMeld uses MongoDB with a normalized schema design to handle music data from multiple streaming services. The architecture solves the "wide document problem" by separating concerns into focused collections.

## Collection Schema Design

### 1. Raw Playlists Collection (`raw_playlists`)

**Purpose**: Store original, unprocessed playlist data from each streaming service

```json
{
  "_id": "spotify_dance_playlist",
  "service_name": "Spotify",
  "genre_name": "dance",
  "playlist_name": "Dance Hits 2024",
  "playlist_url": "https://open.spotify.com/playlist/...",
  "playlist_cover_url": "https://i.scdn.co/image/...",
  "playlist_cover_description_text": "The biggest dance tracks right now",
  "tracks": [
    {
      "track_name": "Talk To Me",
      "artist_name": "Champion, Four Tet, Skrillex & Naisha",
      "track_url": "https://open.spotify.com/track/...",
      "album_cover_url": "https://i.scdn.co/image/...",
      "rank": 1
    }
  ],
  "insert_timestamp": "2024-06-14T10:30:00Z"
}
```

### 2. Normalized Track Collection (`track`)

**Purpose**: Store complete track metadata with service-specific data

```json
{
  "_id": "USA2P2446028",
  "isrc": "USA2P2446028",
  "apple_music_track_data": {
    "service_name": "AppleMusic",
    "track_name": "Talk To Me",
    "artist_name": "Champion, Four Tet, Skrillex & Naisha",
    "track_url": "https://music.apple.com/us/album/...",
    "album_cover_url": "https://is1-ssl.mzstatic.com/image/..."
  },
  "spotify_track_data": {
    "service_name": "Spotify",
    "track_name": "Talk To Me",
    "artist_name": "Champion, Four Tet, Skrillex & Naisha",
    "track_url": "https://open.spotify.com/track/...",
    "album_cover_url": "https://i.scdn.co/image/..."
  },
  "soundcloud_track_data": {
    "service_name": "SoundCloud",
    "track_name": "Talk To Me",
    "artist_name": "Champion, Four Tet, Skrillex & Naisha",
    "track_url": "https://soundcloud.com/...",
    "album_cover_url": "https://i1.sndcdn.com/artworks-..."
  },
  "youtube_url": "https://www.youtube.com/watch?v=Zbf7WsypIkc",
  "spotify_view": {
    "service_name": "Spotify",
    "start_view": {
      "view_count": 15420000,
      "timestamp": "2024-06-01T00:00:00Z"
    },
    "current_view": {
      "view_count": 15892340,
      "timestamp": "2024-06-14T10:30:00Z"
    },
    "historical_view": [
      {
        "total_view_count": 15420000,
        "delta_view_count": 0,
        "timestamp": "2024-06-01T00:00:00Z"
      },
      {
        "total_view_count": 15892340,
        "delta_view_count": 472340,
        "timestamp": "2024-06-14T10:30:00Z"
      }
    ]
  },
  "youtube_view": {
    "service_name": "YouTube",
    "current_view": {
      "view_count": 8934521,
      "timestamp": "2024-06-14T10:30:00Z"
    }
  },
  "insert_timestamp": "2024-06-14T10:30:00Z",
  "update_timestamp": "2024-06-14T10:30:00Z"
}
```

### 3. Track Playlist Collection (`track_playlist`)

**Purpose**: Store service-specific rankings for each genre

```json
{
  "_id": "spotify_dance",
  "service_name": "Spotify",
  "genre_name": "dance",
  "tracks": [
    {
      "isrc": "USA2P2446028",
      "rank": 1,
      "sources": {
        "Spotify": 1
      }
    },
    {
      "isrc": "GB5KW2402411",
      "rank": 2,
      "sources": {
        "Spotify": 2
      }
    }
  ],
  "insert_timestamp": "2024-06-14T10:30:00Z"
}
```

### 4. Aggregated Playlist Collection (`track_playlist` with service_name: "Aggregate")

**Purpose**: Store cross-service rankings using ISRC matching

```json
{
  "_id": "aggregate_dance",
  "service_name": "Aggregate",
  "genre_name": "dance",
  "tracks": [
    {
      "isrc": "USA2P2446028",
      "rank": 1,
      "sources": {
        "Spotify": 1,
        "SoundCloud": 3,
        "AppleMusic": 2
      },
      "raw_aggregate_rank": 2,
      "aggregate_service_name": "AppleMusic"
    }
  ],
  "insert_timestamp": "2024-06-14T10:30:00Z"
}
```

### 5. View Counts Playlists Collection (`view_counts_playlists`)

**Purpose**: Optimized collection for frontend analytics display

```json
{
  "_id": "dance_analytics",
  "genre_name": "dance",
  "tracks": [
    {
      "isrc": "USA2P2446028",
      "track_name": "Talk To Me",
      "artist_name": "Champion, Four Tet, Skrillex & Naisha",
      "youtube_url": "https://www.youtube.com/watch?v=Zbf7WsypIkc",
      "album_cover_url": "https://i1.sndcdn.com/artworks-...",
      "view_counts": {
        "Spotify": [
          ["2024-06-01T00:00:00Z", 0],
          ["2024-06-14T10:30:00Z", 472340]
        ],
        "Youtube": [
          ["2024-06-01T00:00:00Z", 0],
          ["2024-06-14T10:30:00Z", 234521]
        ]
      }
    }
  ],
  "insert_timestamp": "2024-06-14T10:30:00Z"
}
```

### 6. Cache Collections

#### ISRC Cache (`isrc_cache`)

```json
{
  "_id": "cache_spotify_track_12345",
  "key": "spotify_track_12345",
  "value": "USA2P2446028",
  "insert_timestamp": "2024-06-14T10:30:00Z"
}
```

#### YouTube URL Cache (`youtube_cache`)

```json
{
  "_id": "cache_USA2P2446028",
  "key": "USA2P2446028",
  "value": "https://www.youtube.com/watch?v=Zbf7WsypIkc",
  "insert_timestamp": "2024-06-14T10:30:00Z"
}
```

## Data Models (Pydantic)

### Core Enums

```python
class GenreName(str, Enum):
    DANCE = "dance"
    RAP = "rap"
    COUNTRY = "country"
    POP = "pop"

class TrackSourceServiceName(str, Enum):
    SPOTIFY = "Spotify"
    SOUNDCLOUD = "SoundCloud"
    APPLE_MUSIC = "AppleMusic"

class PlaylistType(str, Enum):
    SPOTIFY = "Spotify"
    SOUNDCLOUD = "SoundCloud"
    APPLE_MUSIC = "AppleMusic"
    AGGREGATE = "Aggregate"
```

### Track Model

```python
class Track(BaseModel):
    isrc: str
    apple_music_track_data: TrackData
    spotify_track_data: TrackData
    soundcloud_track_data: TrackData
    youtube_url: str | None = None
    spotify_view: ServiceView
    youtube_view: ServiceView
```

### Playlist Model

```python
class Playlist(BaseModel):
    service_name: PlaylistType
    genre_name: GenreName
    tracks: list[TrackRank]
```

## Data Processing Pipeline

### 1. Extraction Phase

- Raw playlist data scraped from each service
- Stored in `raw_playlists` collection
- Preserves original structure for debugging

### 2. Transformation Phase

- ISRCs resolved for each track
- YouTube URLs matched using search API
- Album covers fetched from each service
- Data normalized into `Track` objects

### 3. Aggregation Phase

- Tracks matched across services using ISRC
- Cross-service rankings calculated
- Priority given to: Apple Music → SoundCloud → Spotify
- Results stored in aggregated playlist collection

### 4. Analytics Phase

- View counts scraped from Spotify and YouTube
- Historical data tracked with delta calculations
- Optimized for frontend chart display

## Query Patterns

### Get Playlist Data

```javascript
// Frontend API call
const response = await fetch(`${API_BASE_URL}/playlist-data/dance`);
```

### Get Analytics Data

```javascript
// Chart data with view counts
const response = await fetch(`${API_BASE_URL}/graph-data/dance`);
```

### MongoDB Aggregation Example

```python
# Get top tracks across all services for a genre
pipeline = [
    {"$match": {"service_name": "Aggregate", "genre_name": "dance"}},
    {"$unwind": "$tracks"},
    {"$sort": {"tracks.rank": 1}},
    {"$limit": 50}
]
```

## Performance Considerations

### Indexing Strategy

```javascript
// Recommended indexes
db.track_playlist.createIndex({ service_name: 1, genre_name: 1 });
db.track.createIndex({ isrc: 1 });
db.view_counts_playlists.createIndex({ genre_name: 1 });
```

### Caching Layers

1. **MongoDB Cache Collections** - Persistent caching for expensive operations
2. **Cloudflare KV** - Edge caching for API responses
3. **Application Cache** - In-memory caching for frequently accessed data

### Data Size Management

- Raw playlists: ~50 tracks per genre per service
- Total tracks: ~200 unique ISRCs per genre
- Historical data: Daily snapshots with delta calculations
- Cache collections: Key-value pairs with TTL

## Data Quality Measures

### ISRC Validation

- ISRC format validation (e.g., "USA2P2446028")
- Fallback matching when ISRCs are missing
- Cross-reference with multiple music databases

### View Count Accuracy

- Multiple source verification
- Anomaly detection for sudden spikes
- Historical trend validation

### Data Freshness

- Timestamp tracking for all collections
- ETL pipeline runs on configurable schedule
- Data staleness monitoring

This normalized schema design allows for efficient queries, scalable analytics, and maintains data integrity while supporting the complex cross-service matching requirements of TuneMeld.
