from core import settings
from core.api import cache_api, events_api, health_api
from core.graphql import schema
from core.views import track_views
from django.urls import path
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView
from graphene_django.views import GraphQLView

urlpatterns = [
    path("", track_views.main_view, name="main"),
    path("health/", health_api.health, name="health"),
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.ico", permanent=True)),
    path(
        "edm-events/",
        events_api.get_edm_events,
        name="get_edm_events",
    ),
    path(
        "clear-redis-cache/",
        csrf_exempt(cache_api.clear_redis_cache),
        name="clear_redis_cache",
    ),
    path(
        "gql/",
        csrf_exempt(cache_page(settings.CACHE_TIMEOUT)(GraphQLView.as_view(graphiql=True, schema=schema))),
        name="graphql",
    ),
]
