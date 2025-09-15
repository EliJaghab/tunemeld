from core.constants import GenreName
from core.graphql.schema import schema
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Warm up GraphQL cache by calling queries directly"

    def handle(self, *args, **options):
        schema.execute("query { genres { id name displayName } defaultGenre }")

        schema.execute("query { serviceOrder }")

        for genre in GenreName:
            query = (
                f'query {{ playlistsByGenre(genre: "{genre.value}") '
                f"{{ genreName serviceName playlistName playlistCoverUrl }} }}"
            )
            schema.execute(query)
