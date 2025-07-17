"""Tests for the metadata extractor module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import TPE1, TALB, TIT2, TCON, TDRC, TYER

from mp3_id3_processor.metadata_extractor import MetadataExtractor, ExistingMetadata


class TestExistingMetadata:
    """Test the ExistingMetadata dataclass."""
    
    def test_existing_metadata_creation(self):
        """Test creating ExistingMetadata with basic values."""
        metadata = ExistingMetadata(
            file_path=Path("test.mp3"),
            artist="Test Artist",
            album="Test Album",
            title="Test Title",
            genre="Rock",
            year="2020"
        )
        
        assert metadata.file_path == Path("test.mp3")
        assert metadata.artist == "Test Artist"
        assert metadata.album == "Test Album"
        assert metadata.title == "Test Title"
        assert metadata.genre == "Rock"
        assert metadata.year == "2020"
        assert metadata.has_genre is True
        assert metadata.has_year is True
    
    def test_existing_metadata_normalization(self):
        """Test string normalization in ExistingMetadata."""
        metadata = ExistingMetadata(
            file_path=Path("test.mp3"),
            artist="  Test Artist  ",
            album="",
            title=None,
            genre="   ",
            year="2020"
        )
        
        assert metadata.artist == "Test Artist"
        assert metadata.album is None
        assert metadata.title is None
        assert metadata.genre is None
        assert metadata.year == "2020"
        assert metadata.has_genre is False
        assert metadata.has_year is True
    
    def test_needs_tags_methods(self):
        """Test the needs_* methods."""
        # File with no tags
        metadata = ExistingMetadata(file_path=Path("test.mp3"))
        assert metadata.needs_genre() is True
        assert metadata.needs_year() is True
        assert metadata.needs_any_tags() is True
        
        # File with genre but no year
        metadata = ExistingMetadata(file_path=Path("test.mp3"), genre="Rock")
        assert metadata.needs_genre() is False
        assert metadata.needs_year() is True
        assert metadata.needs_any_tags() is True
        
        # File with all tags
        metadata = ExistingMetadata(file_path=Path("test.mp3"), genre="Rock", year="2020")
        assert metadata.needs_genre() is False
        assert metadata.needs_year() is False
        assert metadata.needs_any_tags() is False
    
    def test_has_lookup_info(self):
        """Test the has_lookup_info method."""
        # No lookup info
        metadata = ExistingMetadata(file_path=Path("test.mp3"))
        assert metadata.has_lookup_info() is False
        
        # Has artist
        metadata = ExistingMetadata(file_path=Path("test.mp3"), artist="Test Artist")
        assert metadata.has_lookup_info() is True
        
        # Has title
        metadata = ExistingMetadata(file_path=Path("test.mp3"), title="Test Title")
        assert metadata.has_lookup_info() is True
        
        # Has both
        metadata = ExistingMetadata(file_path=Path("test.mp3"), artist="Test Artist", title="Test Title")
        assert metadata.has_lookup_info() is True
    
    def test_get_search_terms(self):
        """Test the get_search_terms method."""
        metadata = ExistingMetadata(
            file_path=Path("test.mp3"),
            artist="Test Artist",
            album="Test Album",
            title="Test Title"
        )
        
        terms = metadata.get_search_terms()
        assert terms == {
            'artist': 'Test Artist',
            'album': 'Test Album',
            'title': 'Test Title'
        }
        
        # Test with partial data
        metadata = ExistingMetadata(file_path=Path("test.mp3"), artist="Test Artist")
        terms = metadata.get_search_terms()
        assert terms == {'artist': 'Test Artist'}


class TestMetadataExtractor:
    """Test the MetadataExtractor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = MetadataExtractor()
        self.test_file = Path("test.mp3")
    
    def test_init(self):
        """Test MetadataExtractor initialization."""
        extractor = MetadataExtractor()
        assert extractor is not None
    
    @patch('mp3_id3_processor.metadata_extractor.MP3')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_load_mp3_file_success(self, mock_is_file, mock_exists, mock_mp3):
        """Test successful MP3 file loading."""
        # Mock file existence
        mock_exists.return_value = True
        mock_is_file.return_value = True
        
        # Mock MP3 file
        mock_audio = Mock()
        mock_audio.info = Mock()
        mock_audio.info.length = 180.0
        mock_mp3.return_value = mock_audio
        
        result = self.extractor._load_mp3_file(self.test_file)
        assert result == mock_audio
    
    @patch('mp3_id3_processor.metadata_extractor.MP3')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_load_mp3_file_no_header(self, mock_is_file, mock_exists, mock_mp3):
        """Test loading MP3 file with no ID3 header."""
        # Mock file existence
        mock_exists.return_value = True
        mock_is_file.return_value = True
        
        # Should try again and succeed
        mock_audio = Mock()
        mock_audio.info = Mock()
        mock_audio.info.length = 180.0
        mock_mp3.side_effect = [mutagen.id3.ID3NoHeaderError(), mock_audio]
        
        result = self.extractor._load_mp3_file(self.test_file)
        assert result == mock_audio
    
    @patch('mp3_id3_processor.metadata_extractor.MP3')
    def test_load_mp3_file_header_not_found(self, mock_mp3):
        """Test loading MP3 file with header not found error."""
        mock_mp3.side_effect = mutagen.mp3.HeaderNotFoundError()
        
        result = self.extractor._load_mp3_file(self.test_file)
        assert result is None
    
    @patch('mp3_id3_processor.metadata_extractor.MP3')
    def test_load_mp3_file_invalid_length(self, mock_mp3):
        """Test loading MP3 file with invalid length."""
        mock_audio = Mock()
        mock_audio.info = Mock()
        mock_audio.info.length = 0  # Invalid length
        mock_mp3.return_value = mock_audio
        
        result = self.extractor._load_mp3_file(self.test_file)
        assert result is None
    
    def test_extract_artist(self):
        """Test artist extraction from ID3 tags."""
        # Mock audio file with TPE1 tag
        mock_audio = Mock()
        mock_audio.tags = {
            'TPE1': Mock(text=['Test Artist'])
        }
        
        result = self.extractor._extract_artist(mock_audio)
        assert result == "Test Artist"
        
        # Test with no artist tag
        mock_audio.tags = {}
        result = self.extractor._extract_artist(mock_audio)
        assert result is None
        
        # Test with empty artist tag
        mock_audio.tags = {
            'TPE1': Mock(text=[''])
        }
        result = self.extractor._extract_artist(mock_audio)
        assert result is None
    
    def test_extract_album(self):
        """Test album extraction from ID3 tags."""
        mock_audio = Mock()
        mock_audio.tags = {
            'TALB': Mock(text=['Test Album'])
        }
        
        result = self.extractor._extract_album(mock_audio)
        assert result == "Test Album"
        
        # Test with no album tag
        mock_audio.tags = {}
        result = self.extractor._extract_album(mock_audio)
        assert result is None
    
    def test_extract_title(self):
        """Test title extraction from ID3 tags."""
        mock_audio = Mock()
        mock_audio.tags = {
            'TIT2': Mock(text=['Test Title'])
        }
        
        result = self.extractor._extract_title(mock_audio)
        assert result == "Test Title"
        
        # Test with no title tag
        mock_audio.tags = {}
        result = self.extractor._extract_title(mock_audio)
        assert result is None
    
    def test_extract_genre(self):
        """Test genre extraction from ID3 tags."""
        mock_audio = Mock()
        mock_audio.tags = {
            'TCON': Mock(text=['Rock'])
        }
        
        result = self.extractor._extract_genre(mock_audio)
        assert result == "Rock"
        
        # Test with meaningless genre
        mock_audio.tags = {
            'TCON': Mock(text=['Unknown'])
        }
        result = self.extractor._extract_genre(mock_audio)
        assert result is None
        
        # Test with no genre tag
        mock_audio.tags = {}
        result = self.extractor._extract_genre(mock_audio)
        assert result is None
    
    def test_extract_year(self):
        """Test year extraction from ID3 tags."""
        # Test TDRC tag (ID3v2.4)
        mock_audio = Mock()
        mock_audio.tags = {
            'TDRC': Mock(text=['2020-01-01'])
        }
        
        result = self.extractor._extract_year(mock_audio)
        assert result == "2020"
        
        # Test TYER tag (ID3v2.3)
        mock_audio.tags = {
            'TYER': Mock(text=['2020'])
        }
        
        result = self.extractor._extract_year(mock_audio)
        assert result == "2020"
        
        # Test invalid year
        mock_audio.tags = {
            'TYER': Mock(text=['1800'])  # Too old
        }
        
        result = self.extractor._extract_year(mock_audio)
        assert result is None
        
        # Test no year tag
        mock_audio.tags = {}
        result = self.extractor._extract_year(mock_audio)
        assert result is None
    
    @patch.object(MetadataExtractor, '_load_mp3_file')
    def test_extract_metadata_success(self, mock_load):
        """Test successful metadata extraction."""
        # Mock loaded MP3 file
        mock_audio = Mock()
        mock_audio.tags = {
            'TPE1': Mock(text=['Test Artist']),
            'TALB': Mock(text=['Test Album']),
            'TIT2': Mock(text=['Test Title']),
            'TCON': Mock(text=['Rock']),
            'TDRC': Mock(text=['2020'])
        }
        mock_load.return_value = mock_audio
        
        result = self.extractor.extract_metadata(self.test_file)
        
        assert result is not None
        assert result.file_path == self.test_file
        assert result.artist == "Test Artist"
        assert result.album == "Test Album"
        assert result.title == "Test Title"
        assert result.genre == "Rock"
        assert result.year == "2020"
    
    @patch.object(MetadataExtractor, '_load_mp3_file')
    def test_extract_metadata_load_failure(self, mock_load):
        """Test metadata extraction when file loading fails."""
        mock_load.return_value = None
        
        result = self.extractor.extract_metadata(self.test_file)
        assert result is None
    
    @patch.object(MetadataExtractor, '_load_mp3_file')
    def test_extract_metadata_no_tags(self, mock_load):
        """Test metadata extraction from file with no tags."""
        mock_audio = Mock()
        mock_audio.tags = None
        mock_load.return_value = mock_audio
        
        result = self.extractor.extract_metadata(self.test_file)
        
        assert result is not None
        assert result.artist is None
        assert result.album is None
        assert result.title is None
        assert result.genre is None
        assert result.year is None
    
    @patch.object(MetadataExtractor, '_load_mp3_file')
    def test_extract_metadata_exception(self, mock_load):
        """Test metadata extraction with exception."""
        mock_load.side_effect = Exception("Test error")
        
        result = self.extractor.extract_metadata(self.test_file)
        assert result is None
    
    @patch.object(MetadataExtractor, 'extract_metadata')
    def test_extract_batch_metadata(self, mock_extract):
        """Test batch metadata extraction."""
        files = [Path("test1.mp3"), Path("test2.mp3")]
        
        # Mock successful extraction for first file, failure for second
        metadata1 = ExistingMetadata(file_path=files[0], artist="Artist 1")
        mock_extract.side_effect = [metadata1, None]
        
        result = self.extractor.extract_batch_metadata(files)
        
        assert len(result) == 1
        assert files[0] in result
        assert result[files[0]] == metadata1
        assert files[1] not in result
    
    def test_get_files_needing_tags(self):
        """Test filtering files that need tags."""
        metadata_dict = {
            Path("complete.mp3"): ExistingMetadata(
                file_path=Path("complete.mp3"), 
                genre="Rock", 
                year="2020"
            ),
            Path("needs_genre.mp3"): ExistingMetadata(
                file_path=Path("needs_genre.mp3"), 
                year="2020"
            ),
            Path("needs_year.mp3"): ExistingMetadata(
                file_path=Path("needs_year.mp3"), 
                genre="Rock"
            ),
            Path("needs_both.mp3"): ExistingMetadata(
                file_path=Path("needs_both.mp3")
            )
        }
        
        result = self.extractor.get_files_needing_tags(metadata_dict)
        
        # Should exclude the complete file
        assert len(result) == 3
        assert Path("complete.mp3") not in result
        assert Path("needs_genre.mp3") in result
        assert Path("needs_year.mp3") in result
        assert Path("needs_both.mp3") in result
    
    def test_get_files_with_lookup_info(self):
        """Test filtering files with lookup information."""
        metadata_dict = {
            Path("no_info.mp3"): ExistingMetadata(
                file_path=Path("no_info.mp3")
            ),
            Path("has_artist.mp3"): ExistingMetadata(
                file_path=Path("has_artist.mp3"), 
                artist="Test Artist"
            ),
            Path("has_title.mp3"): ExistingMetadata(
                file_path=Path("has_title.mp3"), 
                title="Test Title"
            ),
            Path("has_both.mp3"): ExistingMetadata(
                file_path=Path("has_both.mp3"), 
                artist="Test Artist", 
                title="Test Title"
            )
        }
        
        result = self.extractor.get_files_with_lookup_info(metadata_dict)
        
        # Should exclude the file with no info
        assert len(result) == 3
        assert Path("no_info.mp3") not in result
        assert Path("has_artist.mp3") in result
        assert Path("has_title.mp3") in result
        assert Path("has_both.mp3") in result


class TestMetadataExtractorIntegration:
    """Integration tests for MetadataExtractor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = MetadataExtractor()
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_extract_metadata_file_not_exists(self, mock_is_file, mock_exists):
        """Test extraction from non-existent file."""
        mock_exists.return_value = False
        mock_is_file.return_value = False
        
        result = self.extractor.extract_metadata(Path("nonexistent.mp3"))
        assert result is None
    
    def test_extract_metadata_edge_cases(self):
        """Test metadata extraction edge cases."""
        # Test with various edge case values
        test_cases = [
            # Empty strings should become None
            ({'TPE1': Mock(text=[''])}, None),
            # Whitespace-only strings should become None
            ({'TPE1': Mock(text=['   '])}, None),
            # Multiple text values - should take first
            ({'TPE1': Mock(text=['Artist 1', 'Artist 2'])}, 'Artist 1'),
        ]
        
        for tags, expected_artist in test_cases:
            with patch.object(self.extractor, '_load_mp3_file') as mock_load:
                mock_audio = Mock()
                mock_audio.tags = tags
                mock_load.return_value = mock_audio
                
                result = self.extractor.extract_metadata(Path("test.mp3"))
                
                assert result.artist == expected_artist