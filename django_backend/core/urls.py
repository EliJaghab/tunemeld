from core import views
from django.urls import path
from django.views.generic import RedirectView

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
]
