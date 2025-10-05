# Local Setup

## System Dependencies

- Python 3.13+
- PostgreSQL
- Redis
- Node.js

## Quick Start

```bash
# Install system deps (macOS)
brew install postgresql redis

# Clone and setup
git clone https://github.com/yourusername/tunemeld.git
cd tunemeld

# Python environment
python3.13 -m venv venv
source venv/bin/activate
pip install -e .

# Frontend deps
cd frontend && npm install && cd ..

# Database
createdb tunemeld
export DATABASE_URL="postgresql://localhost/tunemeld"

# Environment variables
cp .env.example .env.dev
# Edit .env.dev with your API keys

# Run migrations
cd backend && python manage.py migrate && cd ..

# Start everything
make serve
```

## Required Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection (optional, defaults to localhost:6379)
- `CF_ACCOUNT_ID`, `CF_NAMESPACE_ID`, `CF_API_TOKEN` - Cloudflare KV
- `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET` - Spotify API
- `X_RAPIDAPI_KEY_A`, `X_RAPIDAPI_KEY_B` - RapidAPI keys
- `GOOGLE_API_KEY` - YouTube Data API
