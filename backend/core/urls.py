from core.api import cache_api, events_api, health_api
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from strawberry.django.views import GraphQLView

from gql.schema import schema

# API-only endpoints - frontend served by Cloudflare Pages
urlpatterns = [
    path("api/health/", health_api.health, name="health"),
    path("health/", health_api.health, name="health_legacy"),
    path(
        "api/edm-events/",
        events_api.get_edm_events,
        name="get_edm_events",
    ),
    path(
        "edm-events/",
        events_api.get_edm_events,
        name="get_edm_events_legacy",
    ),
    path(
        "api/clear-redis-cache/",
        csrf_exempt(cache_api.clear_redis_cache),
        name="clear_redis_cache",
    ),
    path(
        "clear-redis-cache/",
        csrf_exempt(cache_api.clear_redis_cache),
        name="clear_redis_cache_legacy",
    ),
    path(
        "api/gql/",
        csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=True)),
        name="graphql",
    ),
    path(
        "gql/",
        csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=True)),
        name="graphql_legacy",
    ),
]
