import json

from extractors import write_json_to_file


def read_json_from_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return data

def transform_apple_music_details(data):
    if not data:
        raise ValueError("Data is empty")

    album_details = data.get("album_details")
    if not album_details:
        raise ValueError("Album details not found in data")

    tracks = []
    for key, track_data in album_details.items():
        if key.isdigit():  # Check if the key is a rank number
            try:
                rank = int(key) + 1  # Convert to 1-based index
            except ValueError:
                print(f"Warning: Skipping rank {key} due to conversion error")
                continue

            track_info = {
                "name": track_data.get("name"),
                "artist": track_data.get("artist"),
                "link": track_data.get("link"),
                "rank": rank,
                "album_url": track_data.get("link"),  # Simplification: Using link as album_url
                "source": "apple_music"
            }
            tracks.append(track_info)

    sorted_tracks = sorted(tracks, key=lambda x: x['rank'])
    return sorted_tracks



if __name__ == "__main__":
    data = read_json_from_file("applemusic_danceplaylist_extract.json")
    transformed = transform_apple_music_details(data)
    write_json_to_file(transformed, "applemusic_danceplaylist_transformed.json")
    