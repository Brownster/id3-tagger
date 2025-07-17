
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import time

from mp3_id3_processor.audiodb_client import AudioDBClient, AudioDBMetadata

class TestAudioDBClient(unittest.TestCase):

    def setUp(self):
        self.cache_dir = Path("./test_cache")
        self.client = AudioDBClient(cache_dir=self.cache_dir)

    def tearDown(self):
        if self.cache_dir.exists():
            for item in self.cache_dir.iterdir():
                item.unlink()
            self.cache_dir.rmdir()

    @patch("mp3_id3_processor.audiodb_client.urlopen")
    def test_search_artist_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({
            "artists": [{
                "strGenre": "Rock",
                "strStyle": "Rock/Pop"
            }]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        metadata = self.client.search_artist("Test Artist")
        self.assertIsInstance(metadata, AudioDBMetadata)
        self.assertEqual(metadata.artist, "Test Artist")
        self.assertEqual(metadata.genre, "Rock")

    @patch("mp3_id3_processor.audiodb_client.urlopen")
    def test_search_album_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({
            "album": [{
                "strGenre": "Pop",
                "intYearReleased": "2023"
            }]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        metadata = self.client.search_album("Test Artist", "Test Album")
        self.assertIsInstance(metadata, AudioDBMetadata)
        self.assertEqual(metadata.artist, "Test Artist")
        self.assertEqual(metadata.album, "Test Album")
        self.assertEqual(metadata.genre, "Pop")
        self.assertEqual(metadata.year, "2023")

    @patch("mp3_id3_processor.audiodb_client.urlopen")
    def test_search_track_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({
            "track": [{
                "strAlbum": "Test Album",
                "intYearReleased": "2023"
            }]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        metadata = self.client.search_track("Test Artist", "Test Track")
        self.assertIsInstance(metadata, AudioDBMetadata)
        self.assertEqual(metadata.artist, "Test Artist")
        self.assertEqual(metadata.track, "Test Track")
        self.assertEqual(metadata.album, "Test Album")
        self.assertEqual(metadata.year, "2023")

    def test_caching(self):
        cache_key = "test_key"
        cache_data = {"test": "data"}
        self.client._cache_response(cache_key, cache_data)
        cached_response = self.client._get_cached_response(cache_key)
        self.assertEqual(cached_response, cache_data)

    def test_rate_limiting(self):
        self.client.last_request_time = time.time()
        with patch("time.sleep") as mock_sleep:
            self.client._wait_for_rate_limit()
            mock_sleep.assert_called_once()

if __name__ == "__main__":
    unittest.main()
