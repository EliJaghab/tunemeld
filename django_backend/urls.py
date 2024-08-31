"""
URL configuration for django_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django_backend import views

urlpatterns = [
    path('', views.root, name='root'), 
    path("admin/", admin.site.urls),
    path('graph-data/<str:genre_name>/', views.get_graph_data, name='get_graph_data_by_genre'),
    path('playlist-data/<str:genre_name>/', views.get_playlist_data, name='get_playlist_data_by_genre'),
    path('service-playlist/<str:genre_name>/<str:service_name>/', views.get_service_playlist, name='get_service_playlist_by_genre_and_service'),
    path('last-updated/<str:genre_name>/', views.get_last_updated, name='get_last_updated_by_genre'),
    path('header-art/<str:genre_name>/', views.get_header_art, name='get_header_art_by_genre'),
]

