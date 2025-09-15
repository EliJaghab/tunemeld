from core.constants import GenreName, ServiceName
from core.graphql.schema import schema
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Warm view count GraphQL cache by calling view count queries"

    def handle(self, *args, **options):
        # Warm view count data for TuneMeld playlists (most accessed)
        for genre in GenreName:
            schema.execute(f"""
                query GetPlaylistTracks($genre: String!, $service: String!) {{
                    playlist(genre: "{genre.value}", service: "{ServiceName.TUNEMELD.value}") {{
                        tracks {{
                            isrc
                            youtubeCurrentViewCount
                            spotifyCurrentViewCount
                            youtubeViewCountDeltaPercentage
                            spotifyViewCountDeltaPercentage
                        }}
                    }}
                }}
            """)
