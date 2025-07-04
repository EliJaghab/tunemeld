# Redis Cache Setup for TuneMeld

This document provides comprehensive instructions for setting up and using Redis caching with Railway for the TuneMeld Django backend.

## Overview

The Redis caching system provides high-performance caching for the TuneMeld application, with automatic Railway integration and comprehensive testing support.

## Features

- **Railway Integration**: Automatic Redis URL detection from Railway environment
- **Environment-Specific Configuration**: Different cache settings for development and production
- **Comprehensive Cache Management**: Utility classes for easy cache operations
- **Genre-Based Invalidation**: Bulk cache invalidation for specific genres
- **Debug Endpoints**: Built-in endpoints for cache status and debugging
- **Extensive Testing**: Complete test suite for cache functionality

## Railway Setup

### 1. Add Redis Plugin to Railway Project

1. Go to your Railway project dashboard
2. Click "Add Plugin" → "Redis"
3. Railway will automatically provision Redis and inject the `REDIS_URL` environment variable

### 2. Environment Variables

Railway automatically provides:

- `REDIS_URL`: Connection string for Redis instance
- `RAILWAY_ENVIRONMENT`: Environment indicator (development/production)

## Local Development Setup

### 1. Install Redis Locally

**macOS (using Homebrew):**

```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
```

**Windows:**
Download and install Redis from [Redis Downloads](https://redis.io/downloads)

### 2. Environment Configuration

Create or update your `.env.dev` file:

```env
REDIS_URL=redis://localhost:6379/0
RAILWAY_ENVIRONMENT=development
```

### 3. Install Python Dependencies

```bash
cd django_backend
pip install -r requirements.txt
```

## Usage

### Basic Cache Operations

```python
from core.cache_utils import CacheManager

# Set a value
CacheManager.set("my_key", {"data": "value"}, timeout=300)

# Get a value
data = CacheManager.get("my_key")

# Delete a value
CacheManager.delete("my_key")

# Get or set (with callable)
def expensive_operation():
    return {"computed": "data"}

result = CacheManager.get_or_set("computation_key", expensive_operation, 600)
```

### View-Level Caching

```python
from core.cache_utils import cache_json_response

@cache_json_response(timeout=3600, key_prefix="playlist")
def get_playlist_data(request, genre_name):
    # Your view logic here
    data = fetch_playlist_data(genre_name)
    return JsonResponse(data)
```

### Cache Invalidation

```python
# Invalidate all cache entries for a specific genre
CacheManager.invalidate_genre_cache("dance")

# Manual key deletion
CacheManager.delete("specific_key")

# Clear pattern-based keys
CacheManager.clear_pattern("graph_data:*")
```

## Cache Key Structure

The cache uses a structured key naming convention:

- `graph_data:{genre}` - Graph data by genre
- `playlist_data:{genre}` - Playlist data by genre
- `service_playlist:{genre}:{service}` - Service-specific playlists
- `last_updated:{genre}` - Last updated timestamps
- `header_art:{genre}` - Header art data

## Cache Timeouts

Default timeout values:

- **Graph Data**: 1 hour (3600 seconds)
- **Playlist Data**: 30 minutes (1800 seconds)
- **Service Playlists**: 15 minutes (900 seconds)
- **Last Updated**: 5 minutes (300 seconds)
- **Header Art**: 2 hours (7200 seconds)

## Debug Endpoints

### Cache Status

**Endpoint:** `GET /cache-status/`

Returns cache connection status and configuration information.

**Example Response:**

```json
{
  "status": "success",
  "message": "Cache status retrieved successfully",
  "data": {
    "connected": true,
    "backend": "RedisCache",
    "location": "redis://localhost:6379/0"
  }
}
```

### Cache Debug

**Endpoint:** `GET /cache-debug/`

Performs comprehensive cache testing and returns detailed debug information.

**Example Response:**

```json
{
  "status": "success",
  "message": "Cache debug completed",
  "data": {
    "cache_working": true,
    "test_value_set": { "timestamp": "2024-01-01T00:00:00Z", "test": true },
    "test_value_retrieved": { "timestamp": "2024-01-01T00:00:00Z", "test": true },
    "values_match": true,
    "cache_status": {
      "connected": true,
      "backend": "RedisCache",
      "location": "redis://localhost:6379/0"
    }
  }
}
```

## Testing

### Running Cache Tests

```bash
# Run only cache-specific tests
cd django_backend
python -m pytest core/tests.py::RedisCacheTestCase -v

# Run all Django tests
python -m pytest core/tests.py -v

# Run with coverage
python -m pytest core/tests.py --cov=core --cov-report=term-missing
```

### GitHub Actions Integration

The cache system includes comprehensive GitHub Actions workflows:

- **Automatic Testing**: Runs on every push and pull request
- **Scheduled Testing**: Daily health checks at 6 AM UTC
- **Multiple Python Versions**: Tests against Python 3.9, 3.10, and 3.11
- **Performance Testing**: Load testing and performance benchmarks
- **Integration Testing**: End-to-end cache functionality tests

**Workflow File:** `.github/workflows/cache_testing.yml`

## Production Configuration

### Railway Production Settings

Production environment automatically configures:

- **Higher Timeouts**: 1 hour default for better performance
- **Compression**: Zlib compression for reduced memory usage
- **Connection Pooling**: Optimized connection pool settings
- **Error Handling**: Comprehensive error recovery

### Production Cache Settings

```python
# Production-specific configuration (automatically applied)
CACHES = {
    "default": {
        "TIMEOUT": 3600,  # 1 hour
        "OPTIONS": {
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 50,
                "retry_on_timeout": True,
            }
        }
    }
}
```

## Troubleshooting

### Common Issues

1. **Cache Connection Failed**

   - Check Redis server status
   - Verify `REDIS_URL` environment variable
   - Ensure Redis is running on correct port

2. **Cache Operations Failing**

   - Check Redis server logs
   - Verify connection pool settings
   - Monitor Redis memory usage

3. **Performance Issues**
   - Review cache timeout settings
   - Monitor cache hit rates
   - Consider cache key optimization

### Debug Commands

```bash
# Check Redis connection
redis-cli ping

# Monitor Redis operations
redis-cli monitor

# Check Redis memory usage
redis-cli info memory

# View all cache keys
redis-cli keys "*"

# Clear all cache
redis-cli flushall
```

### Logging

Cache operations are logged with appropriate levels:

- **DEBUG**: Successful cache operations
- **WARNING**: Cache operation failures
- **ERROR**: Critical cache system errors

Enable debug logging in `settings.py`:

```python
LOGGING = {
    "loggers": {
        "core.cache_utils": {
            "level": "DEBUG",
            "handlers": ["console"],
        }
    }
}
```

## Performance Optimization

### Best Practices

1. **Use Appropriate Timeouts**: Set timeouts based on data update frequency
2. **Implement Cache Warming**: Pre-populate cache with frequently accessed data
3. **Monitor Cache Hit Rates**: Aim for >80% cache hit rate
4. **Use Compression**: Enable compression for large data sets
5. **Implement Cache Versioning**: Use version keys for cache busting

### Performance Monitoring

```python
# Monitor cache performance
def monitor_cache_performance():
    import time

    # Test write performance
    start = time.time()
    for i in range(100):
        CacheManager.set(f"perf_test_{i}", {"data": f"test_{i}"}, 60)
    write_time = time.time() - start

    # Test read performance
    start = time.time()
    for i in range(100):
        CacheManager.get(f"perf_test_{i}")
    read_time = time.time() - start

    print(f"Write: {write_time:.2f}s, Read: {read_time:.2f}s")
```

## Security Considerations

1. **Network Security**: Use Redis AUTH or VPC for production
2. **Key Naming**: Use consistent, predictable key naming conventions
3. **Data Encryption**: Consider encrypting sensitive cached data
4. **Access Control**: Limit Redis access to application servers only

## Next Steps

1. **Monitor Cache Performance**: Set up monitoring for cache hit rates and performance
2. **Optimize Cache Keys**: Review and optimize cache key patterns
3. **Implement Cache Warming**: Add cache warming for critical data
4. **Add Cache Metrics**: Implement detailed cache usage metrics
5. **Consider Cache Clustering**: For high-availability deployments

## Support

For issues or questions:

1. Check the debug endpoints: `/cache-status/` and `/cache-debug/`
2. Review GitHub Actions workflow results
3. Check Redis server logs
4. Monitor application logs for cache-related errors

The cache system is designed to be resilient and will fall back to database queries if Redis is unavailable, ensuring application reliability.
