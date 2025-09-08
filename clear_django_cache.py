#!/usr/bin/env python3
"""
Clear Django page cache that's caching GraphQL responses for 7 days
"""

import os
import sys

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

def clear_graphql_cache():
    """Clear Django cache including GraphQL page cache"""
    
    print("🧹 Clearing Django Page Cache (GraphQL responses)")
    print("=" * 60)
    
    # Clear ALL cache
    print("Clearing entire Django cache...")
    cache.clear()
    print("✅ Django cache cleared")
    
    # Also try to clear specific cache keys that might be related to GraphQL
    print("\nClearing potential GraphQL-related cache keys...")
    
    # Try some common GraphQL cache key patterns
    possible_keys = [
        "views.decorators.cache.cache_page",
        "gql",
        "graphql", 
        "playlist",
    ]
    
    for key_pattern in possible_keys:
        try:
            cache.delete_many([key_pattern])
            print(f"✅ Attempted to clear: {key_pattern}")
        except Exception as e:
            print(f"⚠️  Could not clear {key_pattern}: {e}")
    
    print("\n🎉 Cache clearing complete!")
    print("GraphQL responses should now reflect database changes")

if __name__ == "__main__":
    clear_graphql_cache()