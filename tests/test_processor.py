"""Unit tests for ID3 processor functionality."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from mutagen.mp3 import MP3
from mutagen.id3 import TCON, TDRC, TYER, ID3NoHeaderError
import mutagen

from mp3_id3_processor.processor import ID3Processor
from mp3_id3_processor.config import Configuration
from mp3_id3_processor.models import ProcessingResult, ConfigurationSchema


class TestID3Processor:
    """Test cases for ID3Processor class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        config = Mock(spec=Configuration)
        config.default_genre = "Rock"
        config.default_year = "2023"
        return config
    
    @pytest.fixture
    def processor(self, mock_config):
        """Create an ID3Processor instance for testing."""
        return ID3Processor(mock_config)
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_init(self, mock_config):
        """Test ID3Processor initialization."""
        processor = ID3Processor(mock_config)
        assert processor.config == mock_config
    
    @patch('mp3_id3_processor.processor.MP3')
    def test_load_mp3_file_success(self, mock_mp3, processor, temp_dir):
        """Test successful MP3 file loading."""
        test_file = temp_dir / "test.mp3"
        test_file.touch()
        
        # Mock MP3 object with proper info
        mock_audio = Mock()
        mock_audio.tags = Mock()
        mock_audio.info = Mock()
        mock_audio.info.length = 120.0
        mock_mp3.return_value = mock_audio
        
        result = processor._load_mp3_file(test_file)
        
        assert result == mock_audio
        mock_mp3.assert_called_once_with(str(test_file))
    
    @patch('mp3_id3_processor.processor.MP3')
    def test_load_mp3_file_no_tags(self, mock_mp3, processor, temp_dir):
        """Test MP3 file loading when no tags exist."""
        test_file = temp_dir / "test.mp3"
        test_file.touch()
        
        # Mock MP3 object with no tags but valid info
        mock_audio = Mock()
        mock_audio.tags = None
        mock_audio.add_tags = Mock()
        mock_audio.info = Mock()
        mock_audio.info.length = 120.0
        mock_mp3.return_value = mock_audio
        
        result = processor._load_mp3_file(test_file)
        
        assert result == mock_audio
        mock_audio.add_tags.assert_called_once()
    
    @patch('mp3_id3_processor.processor.MP3')
    def test_load_mp3_file_failure(self, mock_mp3, processor, temp_dir):
        """Test MP3 file loading failure."""
        test_file = temp_dir / "test.mp3"
        test_file.touch()
        
        # Mock MP3 to raise exception
        mock_mp3.side_effect = mutagen.MutagenError("Invalid file")
        
        result = processor._load_mp3_file(test_file)
        
        assert result is None
    
    def test_needs_genre_tag_missing(self, processor):
        """Test genre tag detection when tag is missing."""
        mock_audio = Mock()
        mock_audio.tags = {}
        
        result = processor.needs_genre_tag(mock_audio)
        
        assert result is True
    
    def test_needs_genre_tag_empty(self, processor):
        """Test genre tag detection when tag is empty."""
        mock_audio = Mock()
        mock_genre_frame = Mock()
        mock_genre_frame.text = [""]
        mock_audio.tags = {'TCON': mock_genre_frame}
        
        result = processor.needs_genre_tag(mock_audio)
        
        assert result is True
    
    def test_needs_genre_tag_whitespace(self, processor):
        """Test genre tag detection when tag contains only whitespace."""
        mock_audio = Mock()
        mock_genre_frame = Mock()
        mock_genre_frame.text = ["   "]
        mock_audio.tags = {'TCON': mock_genre_frame}
        
        result = processor.needs_genre_tag(mock_audio)
        
        assert result is True
    
    def test_needs_genre_tag_present(self, processor):
        """Test genre tag detection when tag is present."""
        mock_audio = Mock()
        mock_genre_frame = Mock()
        mock_genre_frame.text = ["Rock"]
        mock_audio.tags = {'TCON': mock_genre_frame}
        
        result = processor.needs_genre_tag(mock_audio)
        
        assert result is False
    
    def test_needs_year_tag_missing_both(self, processor):
        """Test year tag detection when both TDRC and TYER are missing."""
        mock_audio = Mock()
        mock_audio.tags = {}
        
        result = processor.needs_year_tag(mock_audio)
        
        assert result is True
    
    def test_needs_year_tag_tdrc_present(self, processor):
        """Test year tag detection when TDRC is present."""
        mock_audio = Mock()
        mock_tdrc_frame = Mock()
        mock_tdrc_frame.text = ["2023"]
        mock_audio.tags = {'TDRC': mock_tdrc_frame}
        
        result = processor.needs_year_tag(mock_audio)
        
        assert result is False
    
    def test_needs_year_tag_tyer_present(self, processor):
        """Test year tag detection when TYER is present."""
        mock_audio = Mock()
        mock_tyer_frame = Mock()
        mock_tyer_frame.text = ["2023"]
        mock_audio.tags = {'TYER': mock_tyer_frame}
        
        result = processor.needs_year_tag(mock_audio)
        
        assert result is False
    
    def test_needs_year_tag_empty_values(self, processor):
        """Test year tag detection when tags exist but are empty."""
        mock_audio = Mock()
        mock_tdrc_frame = Mock()
        mock_tdrc_frame.text = [""]
        mock_tyer_frame = Mock()
        mock_tyer_frame.text = ["   "]
        mock_audio.tags = {'TDRC': mock_tdrc_frame, 'TYER': mock_tyer_frame}
        
        result = processor.needs_year_tag(mock_audio)
        
        assert result is True
    
    @patch('mp3_id3_processor.processor.TCON')
    def test_add_genre_tag(self, mock_tcon, processor):
        """Test adding genre tag."""
        mock_audio = Mock()
        mock_audio.tags = {}
        mock_tcon_instance = Mock()
        mock_tcon.return_value = mock_tcon_instance
        
        processor._add_genre_tag(mock_audio, "Rock")

        mock_tcon.assert_called_once_with(encoding=3, text=["Rock"])
        assert mock_audio.tags['TCON'] == mock_tcon_instance
    
    @patch('mp3_id3_processor.processor.TDRC')
    @patch('mp3_id3_processor.processor.TYER')
    def test_add_year_tag(self, mock_tyer, mock_tdrc, processor):
        """Test adding year tag."""
        mock_audio = Mock()
        mock_audio.tags = {}
        mock_tdrc_instance = Mock()
        mock_tyer_instance = Mock()
        mock_tdrc.return_value = mock_tdrc_instance
        mock_tyer.return_value = mock_tyer_instance
        
        processor._add_year_tag(mock_audio, "2023")

        mock_tdrc.assert_called_once_with(encoding=3, text=["2023"])
        mock_tyer.assert_called_once_with(encoding=3, text=["2023"])
        assert mock_audio.tags['TDRC'] == mock_tdrc_instance
        assert mock_audio.tags['TYER'] == mock_tyer_instance
    
    def test_save_file_safely_success(self, processor, temp_dir):
        """Test successful file saving."""
        test_file = temp_dir / "test.mp3"
        test_file.touch()  # Create the file
        mock_audio = Mock()
        mock_audio.save = Mock()
        
        processor._save_file_safely(mock_audio, test_file)
        
        mock_audio.save.assert_called_once()
    
    def test_save_file_safely_failure(self, processor, temp_dir):
        """Test file saving failure."""
        test_file = temp_dir / "test.mp3"
        test_file.touch()  # Create the file
        mock_audio = Mock()
        mock_audio.save = Mock(side_effect=Exception("Save failed"))
        
        with pytest.raises(Exception, match="Unexpected error when saving.*Save failed"):
            processor._save_file_safely(mock_audio, test_file)
    
    @patch.object(ID3Processor, '_load_mp3_file')
    def test_process_file_load_failure(self, mock_load, processor, temp_dir):
        """Test process_file when MP3 loading fails."""
        test_file = temp_dir / "test.mp3"
        mock_load.return_value = None
        
        result = processor.process_file(test_file, genre="Rock", year="2023")

        assert isinstance(result, ProcessingResult)
        assert result.file_path == test_file
        assert result.success is False
        assert result.error_message == "Failed to load MP3 file"
        assert result.tags_added == []
    
    @patch.object(ID3Processor, 'add_missing_tags')
    @patch.object(ID3Processor, 'needs_year_tag')
    @patch.object(ID3Processor, 'needs_genre_tag')
    @patch.object(ID3Processor, '_load_mp3_file')
    def test_process_file_no_tags_needed(self, mock_load, mock_needs_genre, 
                                       mock_needs_year, mock_add_tags, 
                                       processor, temp_dir):
        """Test process_file when no tags need to be added."""
        test_file = temp_dir / "test.mp3"
        mock_audio = Mock()
        mock_load.return_value = mock_audio
        mock_needs_genre.return_value = False
        mock_needs_year.return_value = False
        
        result = processor.process_file(test_file)

        assert result is None
        mock_add_tags.assert_not_called()
    
    @patch.object(ID3Processor, 'add_missing_tags')
    @patch.object(ID3Processor, 'needs_year_tag')
    @patch.object(ID3Processor, 'needs_genre_tag')
    @patch.object(ID3Processor, '_load_mp3_file')
    def test_process_file_tags_added(self, mock_load, mock_needs_genre, 
                                   mock_needs_year, mock_add_tags, 
                                   processor, temp_dir):
        """Test process_file when tags are successfully added."""
        test_file = temp_dir / "test.mp3"
        mock_audio = Mock()
        mock_load.return_value = mock_audio
        mock_needs_genre.return_value = True
        mock_needs_year.return_value = True
        mock_add_tags.return_value = ['genre', 'year']
        
        result = processor.process_file(test_file)
        
        assert isinstance(result, ProcessingResult)
        assert result.file_path == test_file
        assert result.success is True
        assert result.tags_added == ['genre', 'year']
        mock_add_tags.assert_called_once_with(mock_audio, test_file, 'Rock', '2023')
    
    @patch.object(ID3Processor, '_load_mp3_file')
    def test_process_file_exception(self, mock_load, processor, temp_dir):
        """Test process_file when an exception occurs."""
        test_file = temp_dir / "test.mp3"
        mock_load.side_effect = Exception("Unexpected error")
        
        result = processor.process_file(test_file)
        
        assert isinstance(result, ProcessingResult)
        assert result.file_path == test_file
        assert result.success is False
        assert "Unexpected error" in result.error_message
        assert result.tags_added == []
    
    @patch.object(ID3Processor, '_save_file_safely')
    @patch.object(ID3Processor, '_add_year_tag')
    @patch.object(ID3Processor, '_add_genre_tag')
    @patch.object(ID3Processor, 'needs_year_tag')
    @patch.object(ID3Processor, 'needs_genre_tag')
    def test_add_missing_tags_both_needed(self, mock_needs_genre, mock_needs_year,
                                        mock_add_genre, mock_add_year, mock_save,
                                        processor, temp_dir):
        """Test adding both genre and year tags."""
        test_file = temp_dir / "test.mp3"
        mock_audio = Mock()
        mock_needs_genre.return_value = True
        mock_needs_year.return_value = True
        
        result = processor.add_missing_tags(mock_audio, test_file, genre="Rock", year="2023")
        
        assert result == ['genre', 'year']
        mock_add_genre.assert_called_once_with(mock_audio, "Rock")
        mock_add_year.assert_called_once_with(mock_audio, "2023")
        mock_save.assert_called_once_with(mock_audio, test_file)
    
    @patch.object(ID3Processor, '_save_file_safely')
    @patch.object(ID3Processor, '_add_genre_tag')
    @patch.object(ID3Processor, 'needs_year_tag')
    @patch.object(ID3Processor, 'needs_genre_tag')
    def test_add_missing_tags_genre_only(self, mock_needs_genre, mock_needs_year,
                                       mock_add_genre, mock_save,
                                       processor, temp_dir):
        """Test adding only genre tag."""
        test_file = temp_dir / "test.mp3"
        mock_audio = Mock()
        mock_needs_genre.return_value = True
        mock_needs_year.return_value = False
        
        result = processor.add_missing_tags(mock_audio, test_file, genre="Rock")
        
        assert result == ['genre']
        mock_add_genre.assert_called_once_with(mock_audio, "Rock")
        mock_save.assert_called_once_with(mock_audio, test_file)
    
    @patch.object(ID3Processor, 'needs_year_tag')
    @patch.object(ID3Processor, 'needs_genre_tag')
    def test_add_missing_tags_none_needed(self, mock_needs_genre, mock_needs_year,
                                        processor, temp_dir):
        """Test when no tags need to be added."""
        test_file = temp_dir / "test.mp3"
        mock_audio = Mock()
        mock_needs_genre.return_value = False
        mock_needs_year.return_value = False
        
        result = processor.add_missing_tags(mock_audio, test_file)
        
        assert result == []
    
    @patch.object(ID3Processor, '_add_genre_tag')
    @patch.object(ID3Processor, 'needs_year_tag')
    @patch.object(ID3Processor, 'needs_genre_tag')
    def test_add_missing_tags_exception(self, mock_needs_genre, mock_needs_year,
                                      mock_add_genre, processor, temp_dir):
        """Test exception handling in add_missing_tags."""
        test_file = temp_dir / "test.mp3"
        mock_audio = Mock()
        mock_needs_genre.return_value = True
        mock_needs_year.return_value = False
        mock_add_genre.side_effect = Exception("Tag addition failed")
        
        with pytest.raises(Exception, match="Failed to add tags.*Tag addition failed"):
            processor.add_missing_tags(mock_audio, test_file, genre="Rock")
    
    @patch.object(ID3Processor, '_load_mp3_file')
    def test_get_existing_tags_success(self, mock_load, processor, temp_dir):
        """Test getting existing tags from a file."""
        test_file = temp_dir / "test.mp3"
        mock_audio = Mock()
        
        # Mock genre tag
        mock_genre_frame = Mock()
        mock_genre_frame.text = ["Rock", "Alternative"]
        
        # Mock year tags
        mock_tdrc_frame = Mock()
        mock_tdrc_frame.text = ["2023"]
        mock_tyer_frame = Mock()
        mock_tyer_frame.text = ["2023"]
        
        mock_audio.tags = {
            'TCON': mock_genre_frame,
            'TDRC': mock_tdrc_frame,
            'TYER': mock_tyer_frame
        }
        mock_load.return_value = mock_audio
        
        result = processor.get_existing_tags(test_file)
        
        expected = {
            'genre': ['Rock', 'Alternative'],
            'year_tdrc': ['2023'],
            'year_tyer': ['2023']
        }
        assert result == expected
    
    @patch.object(ID3Processor, '_load_mp3_file')
    def test_get_existing_tags_load_failure(self, mock_load, processor, temp_dir):
        """Test getting existing tags when file loading fails."""
        test_file = temp_dir / "test.mp3"
        mock_load.return_value = None
        
        result = processor.get_existing_tags(test_file)
        
        assert result == {}
    
    @patch.object(ID3Processor, '_load_mp3_file')
    def test_get_existing_tags_exception(self, mock_load, processor, temp_dir):
        """Test getting existing tags when an exception occurs."""
        test_file = temp_dir / "test.mp3"
        mock_load.side_effect = Exception("Unexpected error")
        
        result = processor.get_existing_tags(test_file)
        
        assert result == {}


class TestID3ProcessorIntegration:
    """Integration tests for ID3Processor with real Configuration."""
    
    @pytest.fixture
    def real_config(self):
        """Create a real Configuration instance for integration testing."""
        schema = ConfigurationSchema(
            default_genre="Test Genre",
            default_year="2024"
        )
        config = Configuration()
        config._schema = schema
        return config
    
    @pytest.fixture
    def integration_processor(self, real_config):
        """Create an ID3Processor with real configuration."""
        return ID3Processor(real_config)
    
    def test_processor_with_real_config(self, integration_processor):
        """Test that processor works with real configuration."""
        assert integration_processor.config.default_genre == "Test Genre"
        assert integration_processor.config.default_year == "2024"
    
    def test_tag_detection_edge_cases(self, integration_processor):
        """Test edge cases in tag detection logic."""
        # Test with mock audio that has attribute errors
        mock_audio = Mock()
        mock_audio.tags = Mock()
        mock_audio.tags.__contains__ = Mock(side_effect=KeyError("Test error"))
        
        # Should handle exceptions gracefully
        result_genre = integration_processor.needs_genre_tag(mock_audio)
        result_year = integration_processor.needs_year_tag(mock_audio)
        
        assert result_genre is True
        assert result_year is True


class TestID3ProcessorErrorHandling:
    """Test cases for comprehensive error handling in ID3Processor."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        config = Mock(spec=Configuration)
        config.default_genre = "Rock"
        config.default_year = "2023"
        return config
    
    @pytest.fixture
    def processor(self, mock_config):
        """Create an ID3Processor instance for testing."""
        return ID3Processor(mock_config)
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @patch('mp3_id3_processor.processor.MP3')
    def test_load_mp3_file_header_not_found(self, mock_mp3, processor, temp_dir):
        """Test loading MP3 file with HeaderNotFoundError."""
        test_file = temp_dir / "test.mp3"
        test_file.touch()
        
        mock_mp3.side_effect = mutagen.mp3.HeaderNotFoundError("No header found")
        
        result = processor._load_mp3_file(test_file)
        
        assert result is None
    
    @patch('mp3_id3_processor.processor.MP3')
    def test_load_mp3_file_id3_no_header_recoverable(self, mock_mp3, processor, temp_dir):
        """Test loading MP3 file with ID3NoHeaderError that can be recovered."""
        test_file = temp_dir / "test.mp3"
        test_file.touch()
        
        # First call raises ID3NoHeaderError, second call succeeds
        mock_audio = Mock()
        mock_audio.add_tags = Mock()
        mock_mp3.side_effect = [mutagen.id3.ID3NoHeaderError("No ID3 header"), mock_audio]
        
        result = processor._load_mp3_file(test_file)
        
        assert result == mock_audio
        mock_audio.add_tags.assert_called_once()
    
    @patch('mp3_id3_processor.processor.MP3')
    def test_load_mp3_file_id3_no_header_unrecoverable(self, mock_mp3, processor, temp_dir):
        """Test loading MP3 file with ID3NoHeaderError that cannot be recovered."""
        test_file = temp_dir / "test.mp3"
        test_file.touch()
        
        # Both calls raise exceptions
        mock_mp3.side_effect = [
            mutagen.id3.ID3NoHeaderError("No ID3 header"),
            Exception("Cannot add tags")
        ]
        
        result = processor._load_mp3_file(test_file)
        
        assert result is None
    
    @patch('mp3_id3_processor.processor.MP3')
    def test_load_mp3_file_mutagen_error(self, mock_mp3, processor, temp_dir):
        """Test loading file with MutagenError."""
        test_file = temp_dir / "test.mp3"
        test_file.touch()
        
        mock_mp3.side_effect = mutagen.MutagenError("Mutagen error")
        
        result = processor._load_mp3_file(test_file)
        
        assert result is None
    
    @patch('mp3_id3_processor.processor.MP3')
    def test_load_mp3_file_permission_error(self, mock_mp3, processor, temp_dir):
        """Test loading file with PermissionError."""
        test_file = temp_dir / "test.mp3"
        test_file.touch()
        
        mock_mp3.side_effect = PermissionError("Permission denied")
        
        result = processor._load_mp3_file(test_file)
        
        assert result is None
    
    def test_load_mp3_file_nonexistent(self, processor, temp_dir):
        """Test loading non-existent file."""
        test_file = temp_dir / "nonexistent.mp3"
        
        result = processor._load_mp3_file(test_file)
        
        assert result is None
    
    def test_load_mp3_file_not_a_file(self, processor, temp_dir):
        """Test loading a directory instead of a file."""
        test_dir = temp_dir / "not_a_file.mp3"
        test_dir.mkdir()
        
        result = processor._load_mp3_file(test_dir)
        
        assert result is None
    
    @patch('mp3_id3_processor.processor.MP3')
    def test_load_mp3_file_no_audio_info(self, mock_mp3, processor, temp_dir):
        """Test loading MP3 file with no audio info."""
        test_file = temp_dir / "test.mp3"
        test_file.touch()
        
        mock_audio = Mock()
        mock_audio.info = None
        mock_mp3.return_value = mock_audio
        
        result = processor._load_mp3_file(test_file)
        
        assert result is None
    
    @patch('mp3_id3_processor.processor.MP3')
    def test_load_mp3_file_invalid_length(self, mock_mp3, processor, temp_dir):
        """Test loading MP3 file with invalid audio length."""
        test_file = temp_dir / "test.mp3"
        test_file.touch()
        
        mock_audio = Mock()
        mock_audio.info = Mock()
        mock_audio.info.length = 0
        mock_mp3.return_value = mock_audio
        
        result = processor._load_mp3_file(test_file)
        
        assert result is None
    
    @patch('mp3_id3_processor.processor.MP3')
    def test_load_mp3_file_add_tags_fails(self, mock_mp3, processor, temp_dir):
        """Test loading MP3 file when adding tags fails."""
        test_file = temp_dir / "test.mp3"
        test_file.touch()
        
        mock_audio = Mock()
        mock_audio.info = Mock()
        mock_audio.info.length = 120.0
        mock_audio.tags = None
        mock_audio.add_tags = Mock(side_effect=Exception("Cannot add tags"))
        mock_mp3.return_value = mock_audio
        
        result = processor._load_mp3_file(test_file)
        
        assert result is None
    
    def test_save_file_safely_file_not_exists(self, processor, temp_dir):
        """Test saving when file no longer exists."""
        test_file = temp_dir / "nonexistent.mp3"
        mock_audio = Mock()
        
        with pytest.raises(Exception, match="File no longer exists"):
            processor._save_file_safely(mock_audio, test_file)
    
    def test_save_file_safely_not_a_file(self, processor, temp_dir):
        """Test saving when path is not a file."""
        test_dir = temp_dir / "not_a_file.mp3"
        test_dir.mkdir()
        mock_audio = Mock()
        
        with pytest.raises(Exception, match="Path is not a file"):
            processor._save_file_safely(mock_audio, test_dir)
    
    def test_save_file_safely_permission_error(self, processor, temp_dir):
        """Test saving with permission error."""
        test_file = temp_dir / "test.mp3"
        test_file.touch()
        mock_audio = Mock()
        mock_audio.save = Mock(side_effect=PermissionError("Permission denied"))
        
        with pytest.raises(Exception, match="Permission denied - cannot write to file"):
            processor._save_file_safely(mock_audio, test_file)
    
    def test_save_file_safely_no_space_error(self, processor, temp_dir):
        """Test saving with no space left on device."""
        test_file = temp_dir / "test.mp3"
        test_file.touch()
        mock_audio = Mock()
        
        os_error = OSError("No space left on device")
        os_error.errno = 28
        mock_audio.save = Mock(side_effect=os_error)
        
        with pytest.raises(Exception, match="No space left on device when saving"):
            processor._save_file_safely(mock_audio, test_file)
    
    def test_save_file_safely_mutagen_error(self, processor, temp_dir):
        """Test saving with Mutagen error."""
        test_file = temp_dir / "test.mp3"
        test_file.touch()
        mock_audio = Mock()
        mock_audio.save = Mock(side_effect=mutagen.MutagenError("Mutagen error"))
        
        with pytest.raises(Exception, match="Mutagen error when saving"):
            processor._save_file_safely(mock_audio, test_file)
    
    def test_is_supported_file_wrong_extension(self, processor, temp_dir):
        """Test file support check with wrong extension."""
        test_file = temp_dir / "test.wav"
        test_file.touch()
        
        result = processor.is_supported_file(test_file)
        
        assert result is False
    
    def test_is_supported_file_valid_mp3(self, processor, temp_dir):
        """Test file support check with valid MP3."""
        test_file = temp_dir / "test.mp3"
        test_file.touch()
        
        with patch.object(processor, '_load_mp3_file', return_value=Mock()):
            result = processor.is_supported_file(test_file)
            
        assert result is True
    
    def test_is_supported_file_invalid_mp3(self, processor, temp_dir):
        """Test file support check with invalid MP3."""
        test_file = temp_dir / "test.mp3"
        test_file.touch()
        
        with patch.object(processor, '_load_mp3_file', return_value=None):
            result = processor.is_supported_file(test_file)
            
        assert result is False
    
    def test_is_supported_file_exception(self, processor, temp_dir):
        """Test file support check with exception."""
        test_file = temp_dir / "test.mp3"
        test_file.touch()
        
        with patch.object(processor, '_load_mp3_file', side_effect=Exception("Error")):
            result = processor.is_supported_file(test_file)
            
        assert result is False
    
    def test_get_file_error_info_nonexistent(self, processor, temp_dir):
        """Test error info for non-existent file."""
        test_file = temp_dir / "nonexistent.mp3"
        
        result = processor.get_file_error_info(test_file)
        
        assert result == "File does not exist"
    
    def test_get_file_error_info_not_a_file(self, processor, temp_dir):
        """Test error info for directory."""
        test_dir = temp_dir / "not_a_file.mp3"
        test_dir.mkdir()
        
        result = processor.get_file_error_info(test_dir)
        
        assert result == "Path is not a regular file"
    
    def test_get_file_error_info_empty_file(self, processor, temp_dir):
        """Test error info for empty file."""
        test_file = temp_dir / "empty.mp3"
        test_file.touch()
        
        result = processor.get_file_error_info(test_file)
        
        assert result == "File is empty"
    
    def test_get_file_error_info_wrong_extension(self, processor, temp_dir):
        """Test error info for wrong file extension."""
        test_file = temp_dir / "test.wav"
        test_file.write_text("dummy content")
        
        result = processor.get_file_error_info(test_file)
        
        assert result == "Unsupported file extension: .wav"
    
    @patch('mp3_id3_processor.processor.MP3')
    def test_get_file_error_info_header_not_found(self, mock_mp3, processor, temp_dir):
        """Test error info for MP3 header not found."""
        test_file = temp_dir / "test.mp3"
        test_file.write_text("dummy content")
        
        mock_mp3.side_effect = mutagen.mp3.HeaderNotFoundError("No header")
        
        result = processor.get_file_error_info(test_file)
        
        assert result == "MP3 header not found (corrupted or not an MP3 file)"
    
    @patch('mp3_id3_processor.processor.MP3')
    def test_get_file_error_info_id3_no_header(self, mock_mp3, processor, temp_dir):
        """Test error info for ID3 no header."""
        test_file = temp_dir / "test.mp3"
        test_file.write_text("dummy content")
        
        mock_mp3.side_effect = mutagen.id3.ID3NoHeaderError("No ID3 header")
        
        result = processor.get_file_error_info(test_file)
        
        assert result == "No ID3 header found (valid MP3 but no metadata)"
    
    @patch('mp3_id3_processor.processor.MP3')
    def test_get_file_error_info_mutagen_error(self, mock_mp3, processor, temp_dir):
        """Test error info for mutagen error."""
        test_file = temp_dir / "test.mp3"
        test_file.write_text("dummy content")
        
        mock_mp3.side_effect = mutagen.MutagenError("Mutagen error")
        
        result = processor.get_file_error_info(test_file)
        
        assert result == "Mutagen parsing error: Mutagen error"
    
    @patch('mp3_id3_processor.processor.MP3')
    def test_get_file_error_info_no_audio_info(self, mock_mp3, processor, temp_dir):
        """Test error info for file with no audio info."""
        test_file = temp_dir / "test.mp3"
        test_file.write_text("dummy content")
        
        mock_audio = Mock()
        mock_audio.info = None
        mock_mp3.return_value = mock_audio
        
        result = processor.get_file_error_info(test_file)
        
        assert result == "File has no audio information (possibly corrupted)"
    
    @patch('mp3_id3_processor.processor.MP3')
    def test_get_file_error_info_invalid_length(self, mock_mp3, processor, temp_dir):
        """Test error info for file with invalid audio length."""
        test_file = temp_dir / "test.mp3"
        test_file.write_text("dummy content")
        
        mock_audio = Mock()
        mock_audio.info = Mock()
        mock_audio.info.length = 0
        mock_mp3.return_value = mock_audio
        
        result = processor.get_file_error_info(test_file)
        
        assert result == "File has invalid audio length (possibly corrupted)"
    
    @patch('mp3_id3_processor.processor.MP3')
    def test_get_file_error_info_valid_file(self, mock_mp3, processor, temp_dir):
        """Test error info for valid file."""
        test_file = temp_dir / "test.mp3"
        test_file.write_text("dummy content")
        
        mock_audio = Mock()
        mock_audio.info = Mock()
        mock_audio.info.length = 120.0
        mock_mp3.return_value = mock_audio
        
        result = processor.get_file_error_info(test_file)
        
        assert result == "File appears to be valid"
    
    @patch('mp3_id3_processor.processor.MP3')
    def test_get_file_error_info_permission_error(self, mock_mp3, processor, temp_dir):
        """Test error info for permission error."""
        test_file = temp_dir / "test.mp3"
        test_file.write_text("dummy content")
        
        mock_mp3.side_effect = PermissionError("Permission denied")
        
        result = processor.get_file_error_info(test_file)
        
        assert result == "Permission denied - cannot read file"
    
    @patch('mp3_id3_processor.processor.MP3')
    def test_get_file_error_info_unexpected_error(self, mock_mp3, processor, temp_dir):
        """Test error info for unexpected error."""
        test_file = temp_dir / "test.mp3"
        test_file.write_text("dummy content")
        
        mock_mp3.side_effect = Exception("Unexpected error")
        
        result = processor.get_file_error_info(test_file)
        
        assert result == "Unexpected error: Unexpected error"