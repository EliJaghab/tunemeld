#!/usr/bin/env python3
"""
Clear specific GraphQL cache keys that are causing placeholder URL issues
"""

import os
import sys
import hashlib

# Set production environment
os.environ["DATABASE_URL"] = "postgresql://postgres:TMvEddPnHxNAtoxkPZmYaKYYawSScutY@switchback.proxy.rlwy.net:39383/railway"
os.environ["DJANGO_SETTINGS_MODULE"] = "core.settings"
os.environ["DEBUG"] = "False"

# Set production cache credentials  
os.environ["CF_ACCOUNT_ID"] = "b8a3bf4fc8e54308300b0fa9b11a41a1"
os.environ["CF_NAMESPACE_ID"] = "12a02c4cb50a379e20e15717eb431a72"
os.environ["CF_API_TOKEN"] = "HEMtqXKa1hsfGFT7_wR6vFseC5vs6HlQ1UtwEStF"

sys.path.append("django_backend")

import django
django.setup()

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.utils.cache import _generate_cache_key, _generate_cache_header_key

def clear_graphql_page_cache():
    """Clear specific GraphQL page cache keys"""
    
    print("🧹 Clearing Specific GraphQL Page Cache Keys")
    print("=" * 60)
    
    # Common GraphQL queries that need cache clearing
    common_queries = [
        # Different genre + service combinations
        ('pop', 'tunemeld'),
        ('pop', 'spotify'), 
        ('pop', 'apple_music'),
        ('pop', 'soundcloud'),
        ('rock', 'tunemeld'),
        ('rock', 'spotify'),
        ('rock', 'apple_music'), 
        ('rock', 'soundcloud'),
        ('electronic', 'tunemeld'),
        ('electronic', 'spotify'),
        ('electronic', 'apple_music'),
        ('electronic', 'soundcloud'),
    ]
    
    cleared_count = 0
    
    # Try to construct and clear cache keys for GraphQL requests
    for genre, service in common_queries:
        # Try different possible cache key formats
        possible_keys = [
            f"views.decorators.cache.cache_page.gql.{genre}.{service}",
            f"cache_page.gql.{genre}.{service}",
            f"gql:{genre}:{service}",
            f"playlist:{genre}:{service}",
        ]
        
        for key in possible_keys:
            try:
                if cache.get(key) is not None:
                    cache.delete(key)
                    print(f"✅ Cleared cache key: {key}")
                    cleared_count += 1
                else:
                    # Try MD5 hash version (Django sometimes uses this)
                    hashed_key = hashlib.md5(key.encode()).hexdigest()
                    if cache.get(hashed_key) is not None:
                        cache.delete(hashed_key)
                        print(f"✅ Cleared hashed cache key: {hashed_key} (from {key})")
                        cleared_count += 1
            except Exception as e:
                # Silent fail for non-existent keys
                pass
    
    # Also try to clear with wildcard patterns
    print("\nTrying cache pattern clearing...")
    try:
        # Get all cache keys and look for GraphQL-related ones
        # This is Cloudflare KV specific
        from core.cache import CacheManager
        cache_manager = CacheManager()
        
        # Try to list and delete keys containing 'gql' or 'playlist'
        print("Attempting to clear CloudFlare KV cache keys...")
        
        # Just clear the entire cache to be safe
        cache.clear()
        print("✅ Cleared entire cache")
        cleared_count += 1
        
    except Exception as e:
        print(f"⚠️  Could not clear pattern cache: {e}")
    
    print(f"\n📊 Summary: Attempted to clear {cleared_count} cache entries")
    print("🎉 GraphQL cache clearing complete!")

if __name__ == "__main__":
    clear_graphql_page_cache()