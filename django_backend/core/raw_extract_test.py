from core.management.commands.raw_extract import Command
from core.models import Genre, Service
from django.test import TestCase


class RawExtractCommandTest(TestCase):
    def setUp(self):
        self.command = Command()
        self.command.initialize_lookup_tables()

    def test_initialize_lookup_tables(self):
        expected_genres = [
            ("dance", "Dance/Electronic"),
            ("rap", "Hip-Hop/Rap"),
            ("country", "Country"),
            ("pop", "Pop"),
        ]

        self.assertEqual(Genre.objects.count(), len(expected_genres))

        for genre_name, display_name in expected_genres:
            genre = Genre.objects.get(name=genre_name)
            self.assertEqual(genre.display_name, display_name)

        expected_services = [
            ("Spotify", "Spotify"),
            ("AppleMusic", "AppleMusic"),
            ("SoundCloud", "SoundCloud"),
        ]

        self.assertEqual(Service.objects.count(), len(expected_services))

        for service_name, display_name in expected_services:
            service = Service.objects.get(name=service_name)
            self.assertEqual(service.display_name, display_name)

    def test_initialize_lookup_tables_idempotent(self):
        self.command.initialize_lookup_tables()

        self.assertEqual(Genre.objects.count(), 4)
        self.assertEqual(Service.objects.count(), 3)

        self.assertTrue(Genre.objects.filter(name="dance", display_name="Dance/Electronic").exists())
        self.assertTrue(Service.objects.filter(name="Spotify", display_name="Spotify").exists())

    def test_genres_have_correct_attributes(self):
        dance_genre = Genre.objects.get(name="dance")

        self.assertEqual(str(dance_genre), "Dance/Electronic")

        self.assertEqual(dance_genre.name, "dance")
        self.assertEqual(dance_genre.display_name, "Dance/Electronic")
        self.assertIsNotNone(dance_genre.id)

    def test_services_have_correct_attributes(self):
        spotify_service = Service.objects.get(name="Spotify")

        self.assertEqual(str(spotify_service), "Spotify")

        self.assertEqual(spotify_service.name, "Spotify")
        self.assertEqual(spotify_service.display_name, "Spotify")
        self.assertIsNotNone(spotify_service.id)
