# TuneMeld Centralized Configuration

This directory contains the centralized configuration system for TuneMeld, consolidating all settings, constants, and configuration variables into a single, maintainable location.

## Directory Structure

```
config/
├── shared/              # Cross-platform configuration
│   ├── genres.json      # Genre definitions and metadata
│   ├── services.json    # Music service configurations
│   ├── playlists.json   # Playlist URLs and metadata
│   └── constants.json   # UI themes, performance settings, selectors
├── frontend/            # Frontend-specific configuration
│   └── config.js        # Frontend configuration loader
├── backend/             # Backend-specific configuration
│   └── settings.py      # Backend configuration loader
├── environments/        # Environment-specific settings
│   ├── development.json # Development environment
│   ├── production.json  # Production environment
│   └── test.json        # Testing environment
└── README.md           # This file
```

## Usage

### Frontend (JavaScript)

```javascript
import config from "./config/frontend/config.js";

// Get genres
const genres = config.getGenres();
const defaultGenre = config.getDefaultGenre();

// Get service information
const spotifyColor = config.getServiceColor("spotify");
const embedUrl = config.getEmbedUrl("spotify");

// Get playlist URLs
const playlistUrl = config.getPlaylistUrl("spotify", "pop");

// Get API endpoints
const apiBaseUrl = config.getApiBaseUrl();

// Get theme colors
const darkTheme = config.getTheme(true);
```

### Backend (Python)

```python
from config.backend.settings import tunemeld_config, GENRES, SERVICES

# Get genres and services
genres = tunemeld_config.get_genres()
services = tunemeld_config.get_services()

# Get service API configuration
spotify_api = tunemeld_config.get_service_api_config('spotify')

# Get playlist information
playlist_url = tunemeld_config.get_playlist_url('spotify', 'pop')
playlist_id = tunemeld_config.get_playlist_id('spotify', 'pop')

# Get performance settings
retries = tunemeld_config.get_retries()
retry_delay = tunemeld_config.get_retry_delay()

# Get selectors
spotify_xpath = tunemeld_config.get_spotify_xpath()
```

## Configuration Files

### `shared/genres.json`

Defines available music genres with metadata including display names and default selection.

### `shared/services.json`

Configures music streaming services including:

- Service metadata (name, colors, logos)
- API endpoints and configurations
- Embed URLs and URL patterns
- Service ranking priority

### `shared/playlists.json`

Contains playlist URLs and metadata for each service and genre combination.

### `shared/constants.json`

Stores application constants including:

- UI themes (light/dark mode colors)
- Performance settings (retries, thresholds)
- CSS selectors and XPath expressions
- External service URLs (CDNs, ads)

### `environments/*.json`

Environment-specific configuration including:

- API base URLs
- Database connection strings
- CORS settings
- Feature flags
- Debug settings

## Benefits

1. **Single Source of Truth**: All configuration in one place
2. **Environment Separation**: Clear dev/prod/test configurations
3. **Type Safety**: Structured configuration with validation
4. **Maintainability**: Easy to update service URLs, colors, etc.
5. **Consistency**: Shared constants across frontend and backend
6. **Scalability**: Easy to add new genres, services, or environments

## Migration Guide

When migrating existing code to use this centralized configuration:

1. Replace hardcoded values with config calls
2. Update import statements to use the config modules
3. Remove duplicate configuration files
4. Update environment variables to use the new structure

## Adding New Configuration

### New Genre

1. Add entry to `shared/genres.json`
2. Add playlist URLs to `shared/playlists.json` for each service

### New Service

1. Add service configuration to `shared/services.json`
2. Add playlist URLs to `shared/playlists.json`
3. Update service ranking if needed

### New Environment

1. Create new file in `environments/`
2. Follow existing structure and patterns
3. Update config loaders to handle new environment
