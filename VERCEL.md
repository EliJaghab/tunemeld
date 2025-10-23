# Vercel Configuration

## `vercel.json` Rationale

**Memory: 1024MB** - Django + Redis client initialization needs more than default 512MB. Reduces cold start time by ~20-30%.

**Max Duration: 10s** - GraphQL queries complete in <500ms (served from Redis cache), but 10s provides buffer for cold starts.

**Region: iad1** - Co-locates functions with Redis Cloud instance (US East) to minimize network latency (~5-10ms saved per request).

**Cache-Control: s-maxage=60, stale-while-revalidate=300** - Vercel edge caches API responses for 60s (data updates daily via ETL, safe to cache). Serves stale content for 5min while revalidating. Impact: First request ~1.1s, cached requests ~50-100ms.

**Security Headers** - Standard X-Content-Type-Options, X-Frame-Options, X-XSS-Protection for basic security hardening.
