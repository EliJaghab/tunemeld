"""
This file takes 3 json files of playlists and combines them to identify overlapping tracks on different services.

Below is an example of what one entry in the aggregated playlist looks like when a track is seen on all three platforms.
Note: Its source is duplicated in the additional sources key.
    {
    "isrc": "USUG12402645",
    "name": "Summertime Blues",
    "artist": "Chris Lake, Sammy Virji, Nathan Nicholson",
    "link": "https://soundcloud.com/chrislake/chris-lake-sammy-virji-nathan",
    "rank": 4,
    "album_url": "https://i1.sndcdn.com/artworks-p4XAkRuaHNhD-0-original.jpg",
    "source": "soundcloud"
    "additional_sources":
        {
            "apple_music": "www.apple_music_link.com",
            "soundcloud"" "soundcloud_link.com",
            "spotify": "spotify_link.com"
        }
},
"""
import os

from typing import Dict, List

from extractors import write_json_to_file
from transformers import read_json_from_file
import collections

def aggregate_tracks_by_isrc(services):
    track_aggregate = collections.defaultdict(dict)
    
    for service in services:
        for track in service:
            isrc = track['isrc']
            service = track["source"]
            track_aggregate[isrc][service] = track
    
    filtered_aggregate = {}
    for isrc, sources in track_aggregate.items():
        if len(sources) > 1: 
            filtered_aggregate[isrc] = sources
            
    return filtered_aggregate

def consolidate_tracks(tracks_by_isrc):
    consolidated_tracks = []
    
    rank_priority = ['apple_music', 'soundcloud', 'spotify']
    default_source_priority = ['soundcloud', "apple_music", "spotify"]
    
    for track in tracks_by_isrc.values():
        
        primary_rank_source = None
        for rank_source in rank_priority:
            if rank_source in track:
                primary_rank_source = rank_source
                break
        
        primary_source = None
        for source in default_source_priority:
            if source in track:
                primary_source = source
                break
        
        new_track_entry = track[primary_source].copy()
        new_track_entry['rank'] = track[primary_rank_source]['rank']
        new_track_entry['additional_sources'] = {}
        
        for source, details in track.items():
            new_track_entry['additional_sources'][source] = details['link']
        
        consolidated_tracks.append(new_track_entry)
    
    consolidated_tracks.sort(key=lambda x: x['rank'])

    for index, track in enumerate(consolidated_tracks, start=1):
        track['rank'] = index
            
    return consolidated_tracks         

def read_json_files_from_directory() -> List[Dict]:
    all_data = []
    transformed_files_directory = 'migration/data/transform'
    for filename in os.listdir(transformed_files_directory):
        if filename.endswith('.json'):
            file_path = os.path.join(transformed_files_directory, filename)
            data = read_json_from_file(file_path)
            all_data.append(data)
    return all_data

if __name__ == "__main__":
    loaded_data = read_json_files_from_directory()
    tracks_by_isrc = aggregate_tracks_by_isrc(loaded_data)
    consolidated = consolidate_tracks(tracks_by_isrc)
    base_path = "migration/data/aggregated/"
    os.makedirs(base_path)
    write_json_to_file(consolidated, f"{base_path}/danceplaylist_gold.json")
    
    
    
    
    
    
    
    