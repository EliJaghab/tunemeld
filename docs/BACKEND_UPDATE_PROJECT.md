# TuneMeld Backend Update Project

## Project Overview

This document outlines the work required to complete the migration from static file serving to a proper Django REST API backend for TuneMeld. The Django backend is implemented but not fully deployed, and several data consistency issues need resolution.

## Current State Analysis

### ✅ Completed Work
- Django project structure with REST API endpoints
- MongoDB integration with PyMongo
- Cloudflare KV caching implementation
- Basic error handling and response formatting
- CORS configuration for frontend integration

### ⚠️ Issues Identified
1. **Data Inconsistency**: API responses missing view count data (validated in `validation.ipynb`)
2. **Backend Not Deployed**: Django API exists but not live in production
3. **Frontend Still Using Old API**: Static file generation still in use
4. **Incomplete View Count Integration**: Graph data endpoint not properly querying analytics collection

## Work Items Checklist

### Phase 1: Fix Data Layer Integration

#### 1.1 Resolve View Count Data Issues
- [ ] **Fix Graph Data Endpoint** (`django_backend/core/views.py:25-78`)
  - [ ] Update `get_view_counts()` function to properly query `historical_track_views` collection
  - [ ] Ensure view count data structure matches frontend expectations
  - [ ] Add error handling for missing view count data
  
- [ ] **Test Data Consistency**
  - [ ] Run validation notebook to confirm API parity
  - [ ] Update test cases to cover all data scenarios
  - [ ] Verify all 4 genres return consistent data

**Code Changes Required:**
```python
# In django_backend/core/views.py:51-61
def get_view_counts(isrc_list: List[str]) -> Dict:
    track_views_query = {"isrc": {"$in": isrc_list}}
    track_views = historical_track_views.find(track_views_query, {"_id": False})  # Missing line
    
    isrc_to_track_views = {}
    for track in track_views:
        isrc_to_track_views[track["isrc"]] = track
    return isrc_to_track_views
```

#### 1.2 Update Database Queries
- [ ] **Optimize Collection Queries**
  - [ ] Review all collection references in `django_backend/core/__init__.py:10-14`
  - [ ] Ensure proper indexing for performance
  - [ ] Add connection pooling configuration

- [ ] **Add Data Validation**
  - [ ] Implement Pydantic models for API responses
  - [ ] Add data sanitization for user inputs
  - [ ] Handle edge cases (missing tracks, empty playlists)

### Phase 2: Deploy Backend to Production

#### 2.1 Environment Configuration
- [ ] **Production Settings**
  - [ ] Create `settings_prod.py` with production configurations
  - [ ] Set up environment variables for deployment
  - [ ] Configure static file serving
  - [ ] Set `DEBUG = False` for production

- [ ] **Database Configuration**
  - [ ] Verify MongoDB connection strings
  - [ ] Set up connection pooling
  - [ ] Configure read/write preferences

#### 2.2 Deployment Setup
- [ ] **Choose Deployment Platform**
  - [ ] Railway (recommended - already configured)
  - [ ] Heroku (alternative option)
  - [ ] DigitalOcean App Platform

- [ ] **Deployment Configuration**
  - [ ] Create `Dockerfile` if using containerized deployment
  - [ ] Set up `requirements.txt` with exact versions
  - [ ] Configure `gunicorn` for production WSGI server
  - [ ] Set up health check endpoints

**Required Files:**
```bash
# requirements.txt (already exists)
Django>=3.0,<4.0
django-cors-headers==4.4.0
django_distill==3.2.7
gunicorn==20.1.0
pymongo==4.8.0
python-dotenv==1.0.0
uvicorn==0.30.6

# Procfile (for Railway/Heroku)
web: gunicorn core.wsgi:application --bind 0.0.0.0:$PORT
```

#### 2.3 Domain and SSL Configuration
- [ ] **Set up Domain**
  - [ ] Configure `api.tunemeld.com` DNS records
  - [ ] Set up SSL certificate
  - [ ] Update CORS settings for production domain

- [ ] **Test Production Deployment**
  - [ ] Verify all endpoints are accessible
  - [ ] Test CORS configuration with frontend
  - [ ] Monitor response times and error rates

### Phase 3: Frontend Migration

#### 3.1 Update API Configuration
- [ ] **Switch API Endpoints** (`docs/config.js:1-15`)
  - [ ] Update `useProdBackend` to `true`
  - [ ] Verify `DJANGO_API_BASE_URL` points to production
  - [ ] Test all API calls work with new backend

- [ ] **Remove Static File Dependencies**
  - [ ] Update all fetch calls to use Django API
  - [ ] Remove references to static JSON files
  - [ ] Clean up old API endpoints

#### 3.2 Error Handling and User Experience
- [ ] **Add Loading States**
  - [ ] Implement proper loading indicators
  - [ ] Add error messages for API failures
  - [ ] Implement retry logic for failed requests

- [ ] **Offline Support**
  - [ ] Add service worker for caching
  - [ ] Implement graceful degradation
  - [ ] Cache critical data locally

### Phase 4: Testing and Monitoring

#### 4.1 End-to-End Testing
- [ ] **API Testing**
  - [ ] Test all endpoints with various inputs
  - [ ] Verify response formats match frontend expectations
  - [ ] Load test with expected traffic volumes

- [ ] **Frontend Integration Testing**
  - [ ] Test all user workflows
  - [ ] Verify charts and visualizations work correctly
  - [ ] Test across different browsers and devices

#### 4.2 Monitoring and Logging
- [ ] **Application Monitoring**
  - [ ] Set up application logs with appropriate levels
  - [ ] Monitor API response times
  - [ ] Track error rates and types

- [ ] **Database Monitoring**
  - [ ] Monitor MongoDB connection health
  - [ ] Track query performance
  - [ ] Set up alerts for unusual activity

## Technical Implementation Details

### API Endpoint Updates Required

#### 1. Graph Data Endpoint Fix
**File**: `django_backend/core/views.py:25-78`
**Issue**: Missing query to `historical_track_views` collection
**Solution**:
```python
def get_view_counts(isrc_list: List[str]) -> Dict:
    track_views_query = {"isrc": {"$in": isrc_list}}
    track_views = historical_track_views.find(track_views_query, {"_id": False})
    
    isrc_to_track_views = {}
    for track in track_views:
        isrc_to_track_views[track["isrc"]] = track
    return isrc_to_track_views
```

#### 2. Cache Integration
**File**: `django_backend/core/cache.py:29-39`
**Enhancement**: Add error handling and fallback logic
```python
def put_kv_entry(self, key, value, ttl=3600):
    """Add TTL parameter for cache expiration"""
    try:
        return self.put(key, value)
    except Exception as e:
        logger.warning(f"Cache put failed for key {key}: {e}")
        return None
```

#### 3. Response Formatting
**File**: `django_backend/core/views.py:19-21`
**Enhancement**: Add consistent error responses
```python
def create_response(status: ResponseStatus, message: str, data=None, status_code=200):
    response = JsonResponse({
        "status": status.value, 
        "message": message, 
        "data": data
    })
    response.status_code = status_code
    return response
```

### Database Optimization

#### Required Indexes
```javascript
// MongoDB indexes for optimal performance
db.view_counts_playlists.createIndex({"genre_name": 1})
db.playlists_collection.createIndex({"genre_name": 1})
db.transformed_playlists_collection.createIndex({"genre_name": 1, "service_name": 1})
db.raw_playlists_collection.createIndex({"genre_name": 1})
db.historical_track_views.createIndex({"isrc": 1})
```

#### Connection Configuration
```python
# In django_backend/core/__init__.py
from pymongo import MongoClient
import ssl

mongo_client = MongoClient(
    settings.MONGO_URI,
    maxPoolSize=50,
    serverSelectionTimeoutMS=30000,
    ssl_cert_reqs=ssl.CERT_NONE  # if using self-signed certificates
)
```

## Deployment Checklist

### Pre-Deployment
- [ ] All tests pass locally
- [ ] Environment variables configured
- [ ] Database connections tested
- [ ] Static files collected
- [ ] Security settings reviewed

### Deployment Steps
- [ ] Deploy to staging environment
- [ ] Run database migrations (if any)
- [ ] Test all endpoints in staging
- [ ] Update DNS records
- [ ] Deploy to production
- [ ] Verify production functionality

### Post-Deployment
- [ ] Monitor application logs
- [ ] Check API response times
- [ ] Verify frontend integration
- [ ] Update documentation
- [ ] Notify team of completion

## Risk Mitigation

### Rollback Plan
- [ ] Keep old static file API as backup
- [ ] Implement feature flags for API switching
- [ ] Monitor error rates closely
- [ ] Have database backup before changes

### Performance Considerations
- [ ] Implement rate limiting
- [ ] Add request timeout handling
- [ ] Monitor memory usage
- [ ] Set up CDN for static assets

## Success Criteria

### Technical Metrics
- [ ] All API endpoints return data within 500ms
- [ ] Error rate < 1% for all endpoints
- [ ] 99.9% uptime for production deployment
- [ ] Frontend fully functional with backend API

### Business Metrics
- [ ] No user-facing functionality lost
- [ ] Data consistency maintained across all views
- [ ] Charts and analytics working correctly
- [ ] All 4 genres (dance, pop, rap, country) operational

## Timeline Estimate

- **Phase 1 (Data Layer)**: 2-3 days
- **Phase 2 (Deployment)**: 1-2 days  
- **Phase 3 (Frontend)**: 1-2 days
- **Phase 4 (Testing)**: 1-2 days

**Total Estimated Time**: 5-9 days

This project will complete the architectural migration from static files to a proper API-driven backend, enabling better scalability, real-time updates, and more sophisticated analytics capabilities for TuneMeld.