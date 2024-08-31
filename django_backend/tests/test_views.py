from django.test import TestCase
from django.urls import reverse

class EndpointTests(TestCase):

    def test_root_endpoint(self):
        response = self.client.get(reverse('root'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content)

    def test_get_graph_data(self):
        response = self.client.get(reverse('get_graph_data_by_genre', args=['pop']))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json())

    def test_get_playlist_data(self):
        response = self.client.get(reverse('get_playlist_data_by_genre', args=['pop']))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json())

    def test_get_service_playlist(self):
        response = self.client.get(reverse('get_service_playlist_by_genre_and_service', args=['pop', 'Spotify']))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json())

    def test_get_last_updated(self):
        response = self.client.get(reverse('get_last_updated_by_genre', args=['pop']))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json())

    def test_get_header_art(self):
        response = self.client.get(reverse('get_header_art_by_genre', args=['pop']))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json())
