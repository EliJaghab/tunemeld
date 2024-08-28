from django.http import JsonResponse, HttpResponse
from . import playlists_collection, track_views_collection

def root(request):
    return HttpResponse("Hello, World!")

def get_graph_data(request, genre_name):
    if not genre_name:
        return JsonResponse({'error': 'Genre is required'}, status=400)

    try:
        # Fetch playlists by genre
        playlists = playlists_collection.find({'genre_name': genre_name})

        # Extract ISRCs and associated track details
        isrc_list = [
            {
                'isrc': track['isrc'],
                'track_name': track['track_name'],
                'artist_name': track['artist_name'],
                'youtube_url': track.get('youtube_url', ''),
                'album_cover_url': track.get('album_cover_url', '')
            }
            for playlist in playlists
            for track in playlist['tracks']
            if track.get('isrc')
        ]

        if not isrc_list:
            return JsonResponse({'error': 'No ISRCs found for the specified genre'}, status=404)

        # Fetch view counts for the ISRCs
        track_views_query = {
            'isrc': {'$in': [track['isrc'] for track in isrc_list]}
        }
        track_views = track_views_collection.find(track_views_query)

        # Map track views to the corresponding track details
        response_data = []
        for track in isrc_list:
            view_data = next((view for view in track_views if view['isrc'] == track['isrc']), None)

            spotify_views = [
                [entry['current_timestamp'], entry['delta_count']]
                for entry in view_data.get('view_counts', {}).get('Spotify', [])
            ] if view_data else []

            youtube_views = [
                [entry['current_timestamp'], entry['delta_count']]
                for entry in view_data.get('view_counts', {}).get('Youtube', [])
            ] if view_data else []

            response_data.append({
                'isrc': track['isrc'],
                'track_name': track['track_name'],
                'artist_name': track['artist_name'],
                'youtube_url': track['youtube_url'],
                'album_cover_url': track['album_cover_url'],
                'view_counts': {
                    'Spotify': spotify_views,
                    'Youtube': youtube_views
                }
            })

        return JsonResponse(response_data, safe=False)

    except Exception as error:
        return JsonResponse({'error': str(error)}, status=500)
