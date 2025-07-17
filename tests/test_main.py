"""Integration tests for the main application entry point."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from mp3_id3_processor.main import (
    main, parse_arguments, validate_music_directory, display_summary
)
from mp3_id3_processor.models import ProcessingResults, ProcessingResult
from mp3_id3_processor.config import Configuration


class TestParseArguments:
    """Test command-line argument parsing."""
    
    def test_parse_arguments_defaults(self):
        """Test parsing with no arguments uses defaults."""
        with patch('sys.argv', ['mp3_id3_processor']):
            args = parse_arguments()
            assert args.directory is None
            assert args.config is None
            assert args.verbose is False
            assert args.dry_run is False
    
    def test_parse_arguments_all_options(self):
        """Test parsing with all command-line options."""
        test_args = [
            'mp3_id3_processor',
            '--directory', '/test/music',
            '--config', 'config.json',
            '--verbose',
            '--dry-run'
        ]
        
        with patch('sys.argv', test_args):
            args = parse_arguments()
            assert args.directory == '/test/music'
            assert args.config == 'config.json'
            assert args.verbose is True
            assert args.dry_run is True
    
    def test_parse_arguments_short_options(self):
        """Test parsing with short command-line options."""
        test_args = [
            'mp3_id3_processor',
            '-d', '/test/music',
            '-c', 'test.json',
            '-v'
        ]
        
        with patch('sys.argv', test_args):
            args = parse_arguments()
            assert args.directory == '/test/music'
            assert args.config == 'test.json'
            assert args.verbose is True


class TestValidateMusicDirectory:
    """Test music directory validation."""
    
    def test_validate_existing_directory(self, tmp_path):
        """Test validation of existing accessible directory."""
        music_dir = tmp_path / "music"
        music_dir.mkdir()
        
        assert validate_music_directory(music_dir) is True
    
    def test_validate_nonexistent_directory(self, tmp_path):
        """Test validation of non-existent directory."""
        music_dir = tmp_path / "nonexistent"
        
        with patch('builtins.print') as mock_print:
            assert validate_music_directory(music_dir) is False
            mock_print.assert_called()
    
    def test_validate_file_instead_of_directory(self, tmp_path):
        """Test validation when path is a file, not directory."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        with patch('builtins.print') as mock_print:
            assert validate_music_directory(test_file) is False
            mock_print.assert_called()
    
    @patch('pathlib.Path.iterdir')
    def test_validate_permission_denied(self, mock_iterdir, tmp_path):
        """Test validation when directory access is denied."""
        music_dir = tmp_path / "music"
        music_dir.mkdir()
        
        mock_iterdir.side_effect = PermissionError("Permission denied")
        
        with patch('builtins.print') as mock_print:
            assert validate_music_directory(music_dir) is False
            mock_print.assert_called()


class TestMainFunction:
    """Test the main application function."""
    
    @patch('mp3_id3_processor.main.parse_arguments')
    @patch('mp3_id3_processor.main.Configuration')
    @patch('mp3_id3_processor.main.validate_music_directory')
    @patch('mp3_id3_processor.main.FileScanner')
    @patch('mp3_id3_processor.main.ID3Processor')
    @patch('mp3_id3_processor.main.ProcessingLogger')
    @patch('mp3_id3_processor.main.MetadataExtractor')
    @patch('mp3_id3_processor.main.AudioDBClient')
    def test_main_successful_processing(self, mock_audiodb_client, mock_metadata_extractor,
                                      mock_logger_class, mock_processor_class,
                                      mock_scanner_class, mock_validate_dir,
                                      mock_config_class, mock_parse_args):
        """Test successful main execution with file processing."""
        # Setup mocks
        mock_args = Mock()
        mock_args.config = None
        mock_args.directory = None
        mock_args.verbose = False
        mock_args.dry_run = False
        mock_parse_args.return_value = mock_args
        
        mock_config = Mock()
        mock_config.music_directory = Path("/test/music")
        mock_config.verbose = False
        mock_config.use_api = True
        mock_config.api_cache_dir = None
        mock_config.api_request_delay = 0.5
        mock_config.update_from_dict.return_value = True
        mock_config_class.return_value = mock_config
        
        mock_validate_dir.return_value = True
        
        # Setup scanner mock
        mock_scanner = Mock()
        test_files = [Path("/test/music/song1.mp3"), Path("/test/music/song2.mp3")]
        mock_scanner.scan_directory.return_value = test_files
        mock_scanner_class.return_value = mock_scanner
        
        # Setup metadata extractor mock
        mock_metadata_extractor_instance = Mock()
        mock_metadata_extractor_instance.extract_metadata.return_value = Mock(needs_any_tags=lambda: True, has_lookup_info=lambda: True, artist="art", album="alb", title="ttl", needs_genre=lambda: True, needs_year=lambda: True)
        mock_metadata_extractor.return_value = mock_metadata_extractor_instance

        # Setup audiodb client mock
        mock_audiodb_client_instance = Mock()
        mock_audiodb_client_instance.search_album.return_value = Mock(has_genre=lambda: True, has_year=lambda: True, genre="Rock", year="2023")
        mock_audiodb_client.return_value = mock_audiodb_client_instance

        # Setup processor mock
        mock_processor = Mock()
        mock_processor.add_missing_tags.return_value = ['genre', 'year']
        mock_processor_class.return_value = mock_processor
        
        # Setup logger mock
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger
        
        # Test main function
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Verify successful exit
        assert exc_info.value.code == 0
        
        # Verify components were called correctly
        mock_scanner.scan_directory.assert_called_once_with(mock_config.music_directory)
        assert mock_processor.add_missing_tags.call_count == 2
        mock_logger.log_start.assert_called_once_with(2)
        mock_logger.log_summary.assert_called_once()
    
    @patch('mp3_id3_processor.main.parse_arguments')
    @patch('mp3_id3_processor.main.Configuration')
    @patch('mp3_id3_processor.main.validate_music_directory')
    def test_main_invalid_music_directory(self, mock_validate_dir, mock_config_class, mock_parse_args):
        """Test main function with invalid music directory."""
        mock_args = Mock()
        mock_args.config = None
        mock_args.directory = None
        mock_args.verbose = False
        mock_args.dry_run = False
        mock_parse_args.return_value = mock_args
        
        mock_config = Mock()
        mock_config.music_directory = Path("/nonexistent")
        mock_config.update_from_dict.return_value = True
        mock_config_class.return_value = mock_config
        
        mock_validate_dir.return_value = False
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1
    
    @patch('mp3_id3_processor.main.parse_arguments')
    @patch('mp3_id3_processor.main.Configuration')
    @patch('mp3_id3_processor.main.validate_music_directory')
    @patch('mp3_id3_processor.main.FileScanner')
    def test_main_no_mp3_files_found(self, mock_scanner_class, mock_validate_dir,
                                   mock_config_class, mock_parse_args):
        """Test main function when no MP3 files are found."""
        mock_args = Mock()
        mock_args.config = None
        mock_args.directory = None
        mock_args.verbose = False
        mock_args.dry_run = False
        mock_parse_args.return_value = mock_args
        
        mock_config = Mock()
        mock_config.music_directory = Path("/test/music")
        mock_config.verbose = False
        mock_config.update_from_dict.return_value = True
        mock_config_class.return_value = mock_config
        
        mock_validate_dir.return_value = True
        
        mock_scanner = Mock()
        mock_scanner.scan_directory.return_value = []  # No files found
        mock_scanner_class.return_value = mock_scanner
        
        with patch('builtins.print') as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                main()
        
        assert exc_info.value.code == 0
        mock_print.assert_called()
    
    @patch('mp3_id3_processor.main.parse_arguments')
    @patch('mp3_id3_processor.main.Configuration')
    @patch('mp3_id3_processor.main.validate_music_directory')
    @patch('mp3_id3_processor.main.FileScanner')
    @patch('mp3_id3_processor.main.ID3Processor')
    @patch('mp3_id3_processor.main.ProcessingLogger')
    @patch('mp3_id3_processor.main.MetadataExtractor')
    @patch('mp3_id3_processor.main.AudioDBClient')
    def test_main_dry_run_mode(self, mock_audiodb_client, mock_metadata_extractor, mock_logger_class, mock_processor_class,
                             mock_scanner_class, mock_validate_dir,
                             mock_config_class, mock_parse_args):
        """Test main function in dry-run mode."""
        mock_args = Mock()
        mock_args.config = None
        mock_args.directory = None
        mock_args.verbose = False
        mock_args.dry_run = True  # Enable dry-run mode
        mock_parse_args.return_value = mock_args
        
        mock_config = Mock()
        mock_config.music_directory = Path("/test/music")
        mock_config.verbose = False
        mock_config.use_api = True
        mock_config.api_cache_dir = None
        mock_config.api_request_delay = 0.5
        mock_config.update_from_dict.return_value = True
        mock_config_class.return_value = mock_config
        
        mock_validate_dir.return_value = True
        
        mock_scanner = Mock()
        test_files = [Path("/test/music/song1.mp3")]
        mock_scanner.scan_directory.return_value = test_files
        mock_scanner_class.return_value = mock_scanner
        
        # Setup metadata extractor mock
        mock_metadata_extractor_instance = Mock()
        mock_metadata_extractor_instance.extract_metadata.return_value = Mock(needs_any_tags=lambda: True, has_lookup_info=lambda: True, artist="art", album="alb", title="ttl", needs_genre=lambda: True, needs_year=lambda: True)
        mock_metadata_extractor.return_value = mock_metadata_extractor_instance

        # Setup audiodb client mock
        mock_audiodb_client_instance = Mock()
        mock_audiodb_client_instance.search_album.return_value = Mock(has_genre=lambda: True, has_year=lambda: True, genre="Rock", year="2023")
        mock_audiodb_client.return_value = mock_audiodb_client_instance

        mock_processor = Mock()
        mock_processor.add_missing_tags.return_value = ['genre', 'year']
        mock_processor_class.return_value = mock_processor
        
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger
        
        with patch('builtins.print') as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                main()
        
        assert exc_info.value.code == 0
        # Verify dry-run messages were printed
        mock_print.assert_called()
        # Verify logger.log_summary was NOT called in dry-run mode
        mock_logger.log_summary.assert_not_called()
    
    @patch('mp3_id3_processor.main.parse_arguments')
    def test_main_keyboard_interrupt(self, mock_parse_args):
        """Test main function handles keyboard interrupt gracefully."""
        mock_parse_args.side_effect = KeyboardInterrupt()
        
        with patch('builtins.print') as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                main()
        
        assert exc_info.value.code == 130
        mock_print.assert_called_with("\nApplication interrupted by user")
    
    @patch('mp3_id3_processor.main.parse_arguments')
    @patch('mp3_id3_processor.main.Configuration')
    def test_main_configuration_error(self, mock_config_class, mock_parse_args):
        """Test main function with configuration errors."""
        mock_args = Mock()
        mock_args.config = None
        mock_args.directory = None
        mock_args.verbose = False
        mock_args.dry_run = False
        mock_parse_args.return_value = mock_args
        
        mock_config = Mock()
        mock_config.update_from_dict.return_value = False  # Simulate config error
        mock_config_class.return_value = mock_config
        
        with patch('builtins.print') as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                main()
        
        assert exc_info.value.code == 1
        mock_print.assert_called_with("Error: Invalid configuration values provided")


class TestDisplaySummary:
    """Test the display_summary function."""
    
    def test_display_summary(self):
        """Test display_summary function (currently a pass-through)."""
        results = ProcessingResults(total_files=5)
        # This function currently does nothing, so just verify it doesn't crash
        display_summary(results)


class TestMainIntegration:
    """Integration tests for main function with real components."""
    
    def test_main_with_command_line_overrides(self, tmp_path):
        """Test main function with command-line argument overrides."""
        # Create test music directory with a dummy MP3 file
        music_dir = tmp_path / "music"
        music_dir.mkdir()
        test_mp3 = music_dir / "test.mp3"
        test_mp3.write_bytes(b"fake mp3 content")  # Not a real MP3, but tests file handling
        
        test_args = [
            'mp3_id3_processor',
            '--directory', str(music_dir),
            '--verbose',
            '--dry-run'
        ]
        
        with patch('sys.argv', test_args):
            with patch('mp3_id3_processor.scanner.FileScanner.scan_directory') as mock_scan:
                # Mock scanner to return empty list (no valid MP3s)
                mock_scan.return_value = []
                
                with patch('builtins.print'):
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                
                # Should exit cleanly when no files found
                assert exc_info.value.code == 0
