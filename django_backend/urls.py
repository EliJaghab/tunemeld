from django.contrib import admin
from django.urls import path
from django_distill import distill_path
from django_backend import views

GENRES = ['dance', 'country', 'rap', 'pop']
SERVICES = ['AppleMusic', 'SoundCloud', 'Spotify']

def get_index():
    return None

def get_genre_name_params():
    return [{'genre_name': genre} for genre in GENRES]

def get_genre_service_params():
    return [{'genre_name': genre, 'service_name': service} for genre in GENRES for service in SERVICES]

urlpatterns = [
    path('', views.root, name='root'), 
    path("admin/", admin.site.urls),
    distill_path('graph-data/<str:genre_name>/', views.get_graph_data, name='get_graph_data_by_genre', distill_func=get_genre_name_params),
    distill_path('playlist-data/<str:genre_name>/', views.get_playlist_data, name='get_playlist_data_by_genre', distill_func=get_genre_name_params),
    distill_path('service-playlist/<str:genre_name>/<str:service_name>/', views.get_service_playlist, name='get_service_playlist_by_genre_and_service', distill_func=get_genre_service_params),
    distill_path('last-updated/<str:genre_name>/', views.get_last_updated, name='get_last_updated_by_genre', distill_func=get_genre_name_params),
    distill_path('header-art/<str:genre_name>/', views.get_header_art, name='get_header_art_by_genre', distill_func=get_genre_name_params),
]
