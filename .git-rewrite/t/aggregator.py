from fuzzywuzzy import fuzz

def aggregate_playlists(soundcloud_data, apple_music_data, spotify_data):
    all_tracks = soundcloud_data + apple_music_data + spotify_data

    unique_tracks = {}

    def is_duplicate(track1, track2):
        return fuzz.token_set_ratio(track1['song_title'], track2['song_title']) > 90 and \
               fuzz.token_set_ratio(track1['artist_name'], track2['artist_name']) > 90

    for track in all_tracks:
        key = (track['song_title'], track['artist_name'])
        if key not in unique_tracks:
            unique_tracks[key] = {
                'song_title': track['song_title'],
                'artist_name': track['artist_name'],
                'album_cover_url': track['album_cover_url'],
                'sources': [track.get('source')],
                'track_number': int(track.get('track_number', 0)),
            }
        else:
            if track.get('source') not in unique_tracks[key]['sources']:
                unique_tracks[key]['sources'].append(track.get('source'))

    # Filter out tracks that only appear on one platform
    aggregated_data = [track for track in unique_tracks.values() if len(track['sources']) > 1]

    # Separate tracks that appear on all platforms
    all_platform_tracks = [track for track in aggregated_data if len(track['sources']) == 3]

    # Create a custom sorting function that considers your specified priority order
    def sort_tracks(track):
        key = (track['song_title'], track['artist_name'])
        order = {'apple_music': 0, 'spotify': 1, 'soundcloud': 2}
        platform_score = sum(order.get(src, 3) for src in track['sources'])
        return (-len(track['sources']), platform_score, track['track_number'])

    # Sort tracks based on the custom function, and bring tracks that are on all platforms to the front
    aggregated_data.sort(key=sort_tracks)
    aggregated_data = all_platform_tracks + aggregated_data

    # Remove the duplicates in the final list
    final_aggregated_data = []
    for track in aggregated_data:
        if not any(is_duplicate(track, existing_track) for existing_track in final_aggregated_data):
            final_aggregated_data.append(track)
    
    # Assign ranks starting from 1
    for i, track in enumerate(final_aggregated_data, start=1):
        track['rank'] = i
    
    return final_aggregated_data
