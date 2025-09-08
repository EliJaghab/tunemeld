# View Count System Migration: MongoDB to PostgreSQL

## Executive Summary

This document outlines the complete migration of TuneMeld's view count system from a failing MongoDB-based approach to a robust PostgreSQL solution with proper caching and automated ETL processes.

## Current System Analysis

### Existing Problems Identified

1. **Failing GitHub Actions Workflows**

   - `view_count.yml` and `view_count2.yml` failing consistently since August 2025
   - Missing script files: `playlist_etl/main_view_count.py`, `playlist_etl/view_count.py`, `playlist_etl/historical_view_count.py`
   - Dependency installation failures in GHA environment

2. **Inconsistent Model Definitions**

   - ETLTrack model at `django_backend/core/models/f_track.py:75-89` lacks `spotify_view` and `youtube_view` fields
   - View count utilities at `django_backend/core/utils/view_count_utils.py` expect these missing fields
   - GraphQL layer has `view_count_data_json` field but no resolver implementation

3. **Data Storage Issues**
   - Current MongoDB-based storage using embedded Pydantic models
   - No proper indexing or querying capabilities for analytics
   - Historical data tracking is inconsistent

### Current Data Flow

```
MongoDB ETL Track → Pydantic Models → In-Memory Processing → MongoDB Storage
                                   ↓
                            GraphQL (broken resolver)
                                   ↓
                              Frontend (working UI)
```

### Existing Infrastructure

- **Database Models**: `django_backend/core/models/z_view_counts.py` (Django models exist but unused)
- **ETL Utilities**: `django_backend/core/utils/view_count_utils.py` (functional but expects missing fields)
- **Service Integration**: YouTube API and Spotify web scraping via Selenium
- **Frontend**: Working view count display in `docs/playlist.js` and `docs/index.html`

## Target PostgreSQL Architecture

### New Data Flow

```
PostgreSQL Tables ← Direct ETL Script ← API Services (YouTube/Spotify)
        ↓
    Redis Cache (1-6 hour TTL)
        ↓
    GraphQL Resolver
        ↓
    Frontend (existing UI)
```

### Database Schema Design

#### Primary Tables

**view_counts**: Current view counts per track/service

```sql
CREATE TABLE view_counts (
    isrc VARCHAR(12) NOT NULL,                    -- Track identifier
    service_id INTEGER NOT NULL,                  -- YouTube, Spotify, etc.
    view_count BIGINT NOT NULL,                   -- Current play count
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT view_counts_pk PRIMARY KEY (isrc, service_id),
    CONSTRAINT isrc_format CHECK (isrc ~ '^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$')
);
```

**historical_view_counts**: Time-series data for trend analysis

```sql
CREATE TABLE historical_view_counts (
    id BIGSERIAL PRIMARY KEY,
    isrc VARCHAR(12) NOT NULL,
    service_id INTEGER NOT NULL,
    view_count BIGINT NOT NULL,                   -- Snapshot count
    delta_count BIGINT,                           -- Daily change
    recorded_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_daily_record UNIQUE (isrc, service_id, recorded_date)
);
```

#### Performance Indexes

```sql
-- View counts performance
CREATE INDEX idx_view_counts_service ON view_counts(service_id);
CREATE INDEX idx_view_counts_updated ON view_counts(last_updated);
CREATE INDEX idx_view_counts_count ON view_counts(view_count DESC);

-- Historical data performance
CREATE INDEX idx_historical_recorded_date ON historical_view_counts(recorded_date);
CREATE INDEX idx_historical_service_date ON historical_view_counts(service_id, recorded_date);
CREATE INDEX idx_historical_isrc ON historical_view_counts(isrc);
```

### ETL Process Architecture

#### New ETL Script: `playlist_etl/view_count_etl.py`

**Key Features:**

- Direct PostgreSQL writes (no MongoDB dependency)
- Atomic transactions per track
- Delta calculation for historical tracking
- Comprehensive error handling and logging
- Selenium webdriver management
- YouTube API integration

**Process Flow:**

1. Initialize Django environment and database connections
2. Get all tracks with YouTube/Spotify URLs
3. For each track:
   - Fetch current view count from service
   - Update/create record in `view_counts`
   - Create daily snapshot in `historical_view_counts`
   - Calculate delta from previous day
4. Clean up resources and log results

**Error Handling Strategy:**

- Continue processing on individual track failures
- Log detailed error information
- Use database transactions to prevent partial updates
- Graceful webdriver cleanup

### Caching Strategy

#### Redis Cache Layers

1. **Current View Counts**: `view_count:{isrc}:{service}` (1 hour TTL)
2. **Historical Data**: `historical_views:{isrc}:{service}` (6 hours TTL)
3. **GraphQL Responses**: `gql_view_data:{isrc}` (30 minutes TTL)

#### Cache Invalidation

- ETL process clears relevant cache keys after updates
- GraphQL resolver implements cache-aside pattern
- Frontend can request cache refresh via GraphQL mutation

### GraphQL Integration

#### Enhanced Resolver Implementation

```python
def resolve_view_count_data_json(self, info):
    """
    Returns comprehensive view count data structure:
    {
        "spotify": {
            "current": 123456,
            "last_updated": "2025-01-15T10:30:00Z",
            "historical": [
                {"date": "2025-01-14", "count": 123000, "delta": 500},
                {"date": "2025-01-13", "count": 122500, "delta": 800}
            ]
        },
        "youtube": { ... }
    }
    """
```

**Features:**

- Multi-level caching with Redis
- Efficient database queries with select_related
- Historical data limited to last 30 days
- Comprehensive error handling
- Structured JSON response format

### Deployment Strategy

#### Phase 1: Infrastructure Setup

1. Deploy PostgreSQL schema via Django migration
2. Update existing Django models to use PostgreSQL
3. Create new ETL script with full logging
4. Set up Redis caching infrastructure

#### Phase 2: Parallel Operation

1. Run new ETL alongside existing system
2. Compare data accuracy between systems
3. Monitor performance and error rates
4. Validate GraphQL resolver functionality

#### Phase 3: Cutover

1. Update GraphQL resolvers to use PostgreSQL
2. Enable Redis caching
3. Switch GitHub Actions to new workflow
4. Monitor frontend functionality

#### Phase 4: Cleanup

1. Disable old GitHub Actions workflows
2. Remove MongoDB view count dependencies
3. Clean up unused Pydantic models
4. Update documentation

### Monitoring and Observability

#### ETL Monitoring

- Daily success/failure notifications
- View count delta alerts (unusual spikes/drops)
- Service availability monitoring (YouTube API quotas)
- Database performance metrics

#### Application Monitoring

- GraphQL resolver performance
- Cache hit rates
- Frontend error tracking
- API response times

### Risk Assessment and Mitigation

#### High Risk Items

1. **YouTube API Quota Limits**

   - Mitigation: Implement exponential backoff, distribute requests
   - Fallback: Skip YouTube updates for a day if quota exceeded

2. **Spotify Rate Limiting**

   - Mitigation: Selenium with random delays, IP rotation
   - Fallback: Continue with YouTube-only updates

3. **Database Performance**
   - Mitigation: Proper indexing, connection pooling
   - Monitoring: Query performance tracking

#### Medium Risk Items

1. **Cache Invalidation Issues**
   - Mitigation: Conservative TTLs, manual refresh capability
2. **Migration Data Loss**
   - Mitigation: Backup existing data, parallel validation

### Performance Considerations

#### Database Optimizations

- Composite indexes on frequently queried columns
- Partitioning historical table by date (future enhancement)
- Connection pooling for ETL processes
- Read replicas for analytics queries

#### ETL Optimizations

- Batch database operations where possible
- Parallel processing for independent tracks
- Efficient webdriver reuse
- Compressed response handling

#### Frontend Optimizations

- GraphQL query optimization
- Client-side view count formatting
- Lazy loading for historical data
- Progressive data loading

### Testing Strategy

#### Unit Tests

- ETL script components
- GraphQL resolver logic
- Cache layer functionality
- Delta calculation accuracy

#### Integration Tests

- End-to-end data flow validation
- Service API interaction testing
- Database transaction integrity
- Cache invalidation scenarios

#### Load Testing

- ETL process with full track catalog
- GraphQL resolver under load
- Database performance with large datasets
- Cache performance characteristics

### Maintenance Procedures

#### Daily Operations

- Monitor ETL success/failure logs
- Check view count data quality
- Verify cache performance metrics
- Review API usage quotas

#### Weekly Operations

- Analyze view count trends
- Database maintenance (VACUUM, ANALYZE)
- Cache performance optimization
- Error log analysis

#### Monthly Operations

- Historical data cleanup (retain 1 year)
- Performance benchmarking
- Capacity planning review
- Documentation updates

## Implementation Checklist

### Database Layer

- [ ] Create PostgreSQL migration for view count tables
- [ ] Add appropriate indexes for query performance
- [ ] Update Django models if needed
- [ ] Test database performance with sample data

### ETL Pipeline

- [ ] Create `playlist_etl/view_count_etl.py` script
- [ ] Implement service integrations (YouTube/Spotify)
- [ ] Add comprehensive error handling and logging
- [ ] Create new GitHub Actions workflow

### GraphQL Layer

- [ ] Implement `resolve_view_count_data_json` method
- [ ] Add Redis caching integration
- [ ] Test with existing frontend code
- [ ] Add error handling and monitoring

### Caching Infrastructure

- [ ] Set up Redis caching layers
- [ ] Implement cache invalidation strategy
- [ ] Add cache performance monitoring
- [ ] Test cache behavior under load

### Monitoring & Alerting

- [ ] Set up ETL success/failure alerts
- [ ] Add database performance monitoring
- [ ] Create view count anomaly detection
- [ ] Set up frontend error tracking

### Testing & Validation

- [ ] Create comprehensive test suite
- [ ] Validate data accuracy vs existing system
- [ ] Performance test with full dataset
- [ ] End-to-end integration testing

### Documentation

- [ ] Update API documentation
- [ ] Create operational runbooks
- [ ] Document troubleshooting procedures
- [ ] Update CLAUDE.md with new processes

## Success Metrics

### Technical Metrics

- ETL success rate > 99%
- GraphQL response time < 200ms (95th percentile)
- Cache hit rate > 80%
- Database query time < 50ms average

### Business Metrics

- View count data freshness < 24 hours
- Historical trend accuracy
- Frontend loading performance
- Zero data loss during migration

## Timeline Estimates

- **Database Setup**: 1-2 days
- **ETL Development**: 3-4 days
- **GraphQL Integration**: 2-3 days
- **Testing & Validation**: 3-5 days
- **Deployment & Migration**: 2-3 days
- **Total**: 11-17 days

This migration will transform the view count system from a fragile, failing MongoDB approach to a robust, scalable PostgreSQL solution that supports the existing frontend while providing better performance, reliability, and maintainability.
