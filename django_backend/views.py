from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from . import models  

def root(request):
    return HttpResponse("Hello, World!")

    
def get_graph_data(request, genre_name):
    genre = get_object_or_404(models.Genre, name=genre_name)
    tracks = models.Track.objects.filter(genre=genre)

    track_data = []
    for track in tracks:
        historical_views = models.HistoricalTrackView.objects.filter(isrc=track.isrc)
        view_counts = []
        for view in historical_views:
            view_counts.append({
                'timestamp': view.timestamp.isoformat(),
                'delta_count': view.view_counts['delta_count']
            })

        track_data.append({
            'isrc': track.isrc,
            'track_name': track.track_name,
            'artist_name': track.artist_name,
            'youtube_url': track.youtube_url,
            'album_cover_url': track.album_cover_url,
            'view_counts': view_counts
        })

    return JsonResponse(track_data, safe=False)

