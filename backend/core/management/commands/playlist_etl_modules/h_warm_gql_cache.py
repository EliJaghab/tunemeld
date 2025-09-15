from core.constants import GenreName, ServiceName
from core.graphql.schema import schema
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Warm up GraphQL cache by calling queries that match frontend usage patterns"

    def handle(self, *args, **options):
        # 1. Warm genres query (called on page load)
        schema.execute("""
            query GetAvailableGenres {
                genres {
                    id
                    name
                    displayName
                }
                defaultGenre
            }
        """)

        # 2. Warm playlist metadata queries for each genre (called when browsing genres)
        for genre in GenreName:
            schema.execute(f"""
                query GetPlaylistMetadata($genre: String!) {{
                    serviceOrder
                    playlistsByGenre(genre: "{genre.value}") {{
                        playlistName
                        playlistCoverUrl
                        playlistCoverDescriptionText
                        playlistUrl
                        genreName
                        serviceName
                    }}
                }}
            """)

        # 3. Warm track data for TuneMeld playlists (most accessed)
        for genre in GenreName:
            schema.execute(f"""
                query GetPlaylistTracks($genre: String!, $service: String!) {{
                    playlist(genre: "{genre.value}", service: "{ServiceName.TUNEMELD.value}") {{
                        genreName
                        serviceName
                        tracks {{
                            rank(genre: "{genre.value}", service: "{ServiceName.TUNEMELD.value}")
                            isrc
                            trackName
                            artistName
                            albumName
                            albumCoverUrl
                            youtubeUrl
                            spotifyUrl
                            appleMusicUrl
                            soundcloudUrl
                            youtubeCurrentViewCount
                            spotifyCurrentViewCount
                            spotifySource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            appleMusicSource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            soundcloudSource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            youtubeSource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                        }}
                    }}
                }}
            """)
