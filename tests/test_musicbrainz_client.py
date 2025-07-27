import unittest
from unittest.mock import patch

from mp3_id3_processor.musicbrainz_client import MusicBrainzClient, MusicBrainzMetadata

class TestMusicBrainzClient(unittest.TestCase):
    @patch('mp3_id3_processor.musicbrainz_client.musicbrainzngs.search_recordings')
    def test_get_genre_success(self, mock_search):
        mock_search.return_value = {
            'recording-list': [
                {'tag-list': [{'name': 'Rock', 'count': '2'}]}
            ]
        }
        client = MusicBrainzClient()
        metadata = client.get_genre('Artist', 'Album', 'Track')
        self.assertIsInstance(metadata, MusicBrainzMetadata)
        self.assertEqual(metadata.genre, 'Rock')

    @patch('mp3_id3_processor.musicbrainz_client.musicbrainzngs.search_recordings')
    def test_get_genre_no_result(self, mock_search):
        mock_search.return_value = {'recording-list': []}
        client = MusicBrainzClient()
        metadata = client.get_genre('A', 'B', 'C')
        self.assertIsNone(metadata)

    @patch('mp3_id3_processor.musicbrainz_client.musicbrainzngs.search_recordings')
    def test_get_genre_error(self, mock_search):
        mock_search.side_effect = Exception('fail')
        client = MusicBrainzClient()
        metadata = client.get_genre('A', 'B', 'C')
        self.assertIsNone(metadata)

    @patch('mp3_id3_processor.musicbrainz_client.musicbrainzngs.search_recordings')
    def test_get_metadata_genre_and_year(self, mock_search):
        mock_search.return_value = {
            'recording-list': [
                {
                    'tag-list': [{'name': 'Jazz', 'count': '1'}],
                    'release-list': [{'date': '2001-05-20'}]
                }
            ]
        }
        client = MusicBrainzClient()
        metadata = client.get_metadata('Artist', 'Album', 'Track')
        self.assertIsInstance(metadata, MusicBrainzMetadata)
        self.assertEqual(metadata.genre, 'Jazz')
        self.assertEqual(metadata.year, '2001')

if __name__ == '__main__':
    unittest.main()
