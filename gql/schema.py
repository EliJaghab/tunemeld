import os
from datetime import datetime

import strawberry
from core.utils.redis_cache import CachePrefix, redis_cache_get, redis_cache_set
from django.core.cache import caches
from strawberry.schema.config import StrawberryConfig

from gql.genre import GenreQuery
from gql.play_count import PlayCountQuery
from gql.playlist import PlaylistQuery
from gql.service import ServiceQuery
from gql.track import TrackQuery


@strawberry.type
class DebugInfo:
    redis_url: str
    redis_test_result: str
    cache_test_result: str
    timestamp: str


@strawberry.type
class Query(TrackQuery, PlaylistQuery, ServiceQuery, GenreQuery, PlayCountQuery):
    @strawberry.field
    def debug_redis(self) -> DebugInfo:
        """Debug Redis connectivity in production."""
        redis_url = os.getenv("REDIS_URL", "NOT_SET")
        timestamp = datetime.now().isoformat()

        try:
            # Test Django Redis cache
            redis_cache = caches["redis"]
            test_key = f"debug_test_{timestamp}"
            test_value = f"debug_value_{timestamp}"

            redis_cache.set(test_key, test_value, 60)
            retrieved_value = redis_cache.get(test_key)

            if retrieved_value == test_value:
                redis_test_result = "✅ Basic Redis connectivity works!"
            else:
                redis_test_result = f"❌ Redis test failed: expected '{test_value}', got '{retrieved_value}'"
        except Exception as e:
            redis_test_result = f"❌ Redis connection error: {e!s}"

        try:
            # Test custom cache functions
            test_data = {"debug": True, "timestamp": timestamp}
            redis_cache_set(CachePrefix.GQL_PLAYLIST, f"debug_test_{timestamp}", test_data)
            retrieved_data = redis_cache_get(CachePrefix.GQL_PLAYLIST, f"debug_test_{timestamp}")

            if retrieved_data == test_data:
                cache_test_result = "✅ Custom Redis cache functions work!"
            else:
                cache_test_result = f"❌ Cache test failed: expected '{test_data}', got '{retrieved_data}'"
        except Exception as e:
            cache_test_result = f"❌ Cache function error: {e!s}"

        return DebugInfo(
            redis_url=redis_url,
            redis_test_result=redis_test_result,
            cache_test_result=cache_test_result,
            timestamp=timestamp,
        )


schema = strawberry.Schema(query=Query, config=StrawberryConfig(auto_camel_case=True))
