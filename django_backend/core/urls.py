from core import views
from core.graphql import schema
from django.conf import settings
from django.urls import path
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView
from graphene_django.views import GraphQLView

if settings.ENVIRONMENT == settings.DEV:
    from core.api import playlist_api as api_views
else:
    api_views = views

if settings.ENVIRONMENT == settings.DEV:
    # Staging mode: Only new PostgreSQL endpoints
    urlpatterns = [
        path("", views.root, name="root"),
        path("health/", views.health, name="health"),
        path("favicon.ico", RedirectView.as_view(url="/static/favicon.ico", permanent=True)),
        path(
            "aggregate-playlist/<str:genre_name>",
            api_views.get_aggregate_playlist,
            name="get_aggregate_playlist_by_genre",
        ),
        path(
            "playlist/<str:genre_name>/<str:service_name>",
            api_views.get_playlist,
            name="get_playlist_by_genre_and_service",
        ),
        path(
            "playlist-metadata/<str:genre_name>",
            api_views.get_playlist_metadata,
            name="get_playlist_metadata_by_genre",
        ),
        path(
            "last-updated/<str:genre_name>",
            api_views.get_last_updated,
            name="get_last_updated_by_genre",
        ),
        path(
            "edm-events/",
            views.get_edm_events,
            name="get_edm_events",
        ),
        path(
            "gql/",
            csrf_exempt(cache_page(settings.CACHE_TIMEOUT)(GraphQLView.as_view(graphiql=True, schema=schema))),
            name="graphql",
        ),
    ]
else:
    # Production mode: Legacy MongoDB endpoints
    urlpatterns = [
        path("", views.root, name="root"),
        path("health/", views.health, name="health"),
        path("favicon.ico", RedirectView.as_view(url="/static/favicon.ico", permanent=True)),
        path(
            "graph-data/<str:genre_name>",
            views.get_graph_data,
            name="get_graph_data_by_genre",
        ),
        path(
            "playlist-data/<str:genre_name>",
            views.get_playlist_data,
            name="get_playlist_data_by_genre",
        ),
        path(
            "service-playlist/<str:genre_name>/<str:service_name>",
            views.get_service_playlist,
            name="get_service_playlist_by_genre_and_service",
        ),
        path(
            "last-updated/<str:genre_name>",
            views.get_last_updated,
            name="get_last_updated_by_genre",
        ),
        path(
            "header-art/<str:genre_name>",
            views.get_header_art,
            name="get_header_art_by_genre",
        ),
        path(
            "edm-events/",
            views.get_edm_events,
            name="get_edm_events",
        ),
        path(
            "gql/",
            csrf_exempt(cache_page(settings.CACHE_TIMEOUT)(GraphQLView.as_view(graphiql=True, schema=schema))),
            name="graphql",
        ),
    ]
