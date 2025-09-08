#!/usr/bin/env python3
"""
Test the production GraphQL API to find where youtube.com URLs are coming from
"""

import requests
import json

def test_production_gql():
    """Test the production GraphQL API for YouTube URLs"""
    
    print("🔍 Testing production GraphQL API...")
    print("=" * 60)
    
    # GraphQL endpoint
    url = "https://api.tunemeld.com/gql/"
    
    # Query to get playlist data (the actual query the frontend uses)
    query = """
    query GetPlaylist($genre: String!, $service: String!) {
        playlist(genre: $genre, service: $service) {
            genreName
            serviceName
            tracks {
                isrc
                trackName
                artistName
                albumName
                spotifyUrl
                appleMusicUrl
                youtubeUrl
                soundcloudUrl
                albumCoverUrl
                aggregateRank
                aggregateScore
                updatedAt
            }
        }
    }
    """
    
    variables = {
        "genre": "pop",
        "service": "tunemeld"
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "TuneMeld-Debug/1.0"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            
            if "errors" in data:
                print(f"❌ GraphQL errors: {data['errors']}")
                return
            
            playlist_data = data.get("data", {}).get("playlist", {})
            tracks = playlist_data.get("tracks", [])
            print(f"Found {len(tracks)} tracks in {playlist_data.get('serviceName')} {playlist_data.get('genreName')} playlist")
            
            youtube_placeholder_count = 0
            youtube_real_count = 0
            youtube_none_count = 0
            
            print("\n🎵 Sample tracks:")
            print("-" * 60)
            
            for i, track in enumerate(tracks[:10]):  # First 10 tracks
                youtube_url = track.get("youtubeUrl")
                
                print(f"{i+1:2d}. {track['trackName']} by {track['artistName']}")
                print(f"    YouTube: {youtube_url}")
                
                if youtube_url == "https://youtube.com":
                    youtube_placeholder_count += 1
                    print(f"    ❌ PLACEHOLDER URL FOUND!")
                elif youtube_url and youtube_url.startswith("https://www.youtube.com"):
                    youtube_real_count += 1
                    print(f"    ✅ Real YouTube URL")
                elif youtube_url is None:
                    youtube_none_count += 1
                    print(f"    ⚪ No YouTube URL")
                else:
                    print(f"    ❓ Unexpected URL format: {youtube_url}")
                
                print()
            
            print("📊 YouTube URL Analysis:")
            print(f"   Placeholder URLs (youtube.com): {youtube_placeholder_count}")
            print(f"   Real YouTube URLs: {youtube_real_count}")
            print(f"   No YouTube URL (null): {youtube_none_count}")
            
            if youtube_placeholder_count > 0:
                print(f"\n🚨 ISSUE CONFIRMED: Found {youtube_placeholder_count} placeholder URLs in GraphQL response!")
                print("The GraphQL API is serving 'https://youtube.com' URLs")
            else:
                print("\n✅ No placeholder URLs found in GraphQL response")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    test_production_gql()