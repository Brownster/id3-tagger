"""End-to-end integration tests for the complete MP3 ID3 processor workflow."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock
import json

from mp3_id3_processor.main import main
from mp3_id3_processor.config import Configuration
from mp3_id3_processor.scanner import FileScanner
from mp3_id3_processor.processor import ID3Processor
from mp3_id3_processor.logger import ProcessingLogger
from mp3_id3_processor.models import ProcessingResults, ProcessingResult


class TestEndToEndIntegration:
    """End-to-end integration tests for the complete application workflow."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.music_dir = self.temp_dir / "music"
        self.music_dir.mkdir()
        
    def teardown_method(self):
        """Clean up test environment after each test."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_mock_mp3_files(self, count: int = 3):
        """Create mock MP3 files for testing.
        
        Args:
            count: Number of mock MP3 files to create.
            
        Returns:
            List of created file paths.
        """
        files = []
        for i in range(count):
            mp3_file = self.music_dir / f"song_{i+1}.mp3"
            mp3_file.write_bytes(b"fake mp3 content")
            files.append(mp3_file)
        return files
    
    @patch('mp3_id3_processor.main.FileScanner')
    @patch('mp3_id3_processor.main.ID3Processor')
    def test_complete_workflow_success(self, mock_processor_class, mock_scanner_class):
        """Test complete workflow with successful processing."""
        # Create mock MP3 files
        mp3_files = self.create_mock_mp3_files(3)
        
        # Setup scanner mock
        mock_scanner = Mock()
        mock_scanner.scan_directory.return_value = mp3_files
        mock_scanner_class.return_value = mock_scanner
        
        # Setup processor mock with different scenarios
        mock_processor = Mock()
        results = [
            ProcessingResult(mp3_files[0], True, ["genre"]),  # Added genre
            ProcessingResult(mp3_files[1], True, ["year"]),   # Added year
            ProcessingResult(mp3_files[2], True, [])          # No changes needed
        ]
        mock_processor.process_file.side_effect = results
        mock_processor_class.return_value = mock_processor
        
        # Test arguments
        test_args = [
            'mp3_id3_processor',
            '--directory', str(self.music_dir),
            '--genre', 'TestGenre',
            '--year', '2023',
            '--verbose'
        ]
        
        with patch('sys.argv', test_args):
            with patch('builtins.print') as mock_print:
                with pytest.raises(SystemExit) as exc_info:
                    main()
        
        # Verify successful exit
        assert exc_info.value.code == 0
        
        # Verify all components were called
        mock_scanner.scan_directory.assert_called_once()
        assert mock_processor.process_file.call_count == 3
        
        # Verify output was generated
        mock_print.assert_called()
    
    @patch('mp3_id3_processor.main.FileScanner')
    @patch('mp3_id3_processor.main.ID3Processor')
    def test_complete_workflow_with_errors(self, mock_processor_class, mock_scanner_class):
        """Test complete workflow with some processing errors."""
        # Create mock MP3 files
        mp3_files = self.create_mock_mp3_files(3)
        
        # Setup scanner mock
        mock_scanner = Mock()
        mock_scanner.scan_directory.return_value = mp3_files
        mock_scanner_class.return_value = mock_scanner
        
        # Setup processor mock with mixed results
        mock_processor = Mock()
        results = [
            ProcessingResult(mp3_files[0], True, ["genre"]),     # Success
            ProcessingResult(mp3_files[1], False, [], "Corrupted file"),  # Error
            ProcessingResult(mp3_files[2], True, ["year"])       # Success
        ]
        mock_processor.process_file.side_effect = results
        mock_processor_class.return_value = mock_processor
        
        test_args = [
            'mp3_id3_processor',
            '--directory', str(self.music_dir)
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
        
        # Should exit with code 2 (partial success)
        assert exc_info.value.code == 2
        
        # Verify all files were attempted
        assert mock_processor.process_file.call_count == 3
    
    @patch('mp3_id3_processor.main.FileScanner')
    @patch('mp3_id3_processor.main.ID3Processor')
    def test_dry_run_workflow(self, mock_processor_class, mock_scanner_class):
        """Test complete workflow in dry-run mode."""
        # Create mock MP3 files
        mp3_files = self.create_mock_mp3_files(2)
        
        # Setup mocks
        mock_scanner = Mock()
        mock_scanner.scan_directory.return_value = mp3_files
        mock_scanner_class.return_value = mock_scanner
        
        mock_processor = Mock()
        results = [
            ProcessingResult(mp3_files[0], True, ["genre", "year"]),
            ProcessingResult(mp3_files[1], True, [])
        ]
        mock_processor.process_file.side_effect = results
        mock_processor_class.return_value = mock_processor
        
        test_args = [
            'mp3_id3_processor',
            '--directory', str(self.music_dir),
            '--dry-run',
            '--verbose'
        ]
        
        with patch('sys.argv', test_args):
            with patch('builtins.print') as mock_print:
                with pytest.raises(SystemExit) as exc_info:
                    main()
        
        assert exc_info.value.code == 0
        
        # Verify dry-run specific output
        print_calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        dry_run_messages = [msg for msg in print_calls if "DRY RUN" in msg or "Would add" in msg]
        assert len(dry_run_messages) > 0
    
    def test_configuration_file_integration(self):
        """Test integration with configuration file."""
        # Create configuration file
        config_file = self.temp_dir / "config.json"
        config_data = {
            "default_genre": "ConfigGenre",
            "default_year": "2022",
            "verbose": True
        }
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Create mock MP3 files
        mp3_files = self.create_mock_mp3_files(1)
        
        test_args = [
            'mp3_id3_processor',
            '--directory', str(self.music_dir),
            '--config', str(config_file),
            '--dry-run'
        ]
        
        with patch('mp3_id3_processor.main.FileScanner') as mock_scanner_class:
            with patch('mp3_id3_processor.main.ID3Processor') as mock_processor_class:
                # Setup mocks
                mock_scanner = Mock()
                mock_scanner.scan_directory.return_value = mp3_files
                mock_scanner_class.return_value = mock_scanner
                
                mock_processor = Mock()
                mock_processor.process_file.return_value = ProcessingResult(mp3_files[0], True, ["genre"])
                mock_processor_class.return_value = mock_processor
                
                with patch('sys.argv', test_args):
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                
                assert exc_info.value.code == 0
                
                # Verify processor was initialized with config values
                mock_processor_class.assert_called_once()
                config_arg = mock_processor_class.call_args[0][0]
                assert config_arg.default_genre == "ConfigGenre"
                assert config_arg.default_year == "2022"
    
    @patch('mp3_id3_processor.main.FileScanner')
    def test_scanner_error_handling(self, mock_scanner_class):
        """Test handling of scanner errors in the main workflow."""
        from mp3_id3_processor.scanner import DirectoryAccessError
        
        mock_scanner = Mock()
        mock_scanner.scan_directory.side_effect = DirectoryAccessError("Permission denied")
        mock_scanner_class.return_value = mock_scanner
        
        test_args = [
            'mp3_id3_processor',
            '--directory', str(self.music_dir)
        ]
        
        with patch('sys.argv', test_args):
            with patch('builtins.print') as mock_print:
                with pytest.raises(SystemExit) as exc_info:
                    main()
        
        assert exc_info.value.code == 1
        mock_print.assert_called()
    
    @patch('mp3_id3_processor.main.FileScanner')
    @patch('mp3_id3_processor.main.ID3Processor')
    def test_keyboard_interrupt_during_processing(self, mock_processor_class, mock_scanner_class):
        """Test handling of keyboard interrupt during file processing."""
        # Create mock MP3 files
        mp3_files = self.create_mock_mp3_files(3)
        
        # Setup scanner mock
        mock_scanner = Mock()
        mock_scanner.scan_directory.return_value = mp3_files
        mock_scanner_class.return_value = mock_scanner
        
        # Setup processor mock to raise KeyboardInterrupt on second file
        mock_processor = Mock()
        results = [
            ProcessingResult(mp3_files[0], True, ["genre"]),  # First file succeeds
            KeyboardInterrupt(),  # Second file interrupted
        ]
        mock_processor.process_file.side_effect = results
        mock_processor_class.return_value = mock_processor
        
        test_args = [
            'mp3_id3_processor',
            '--directory', str(self.music_dir)
        ]
        
        with patch('sys.argv', test_args):
            with patch('builtins.print') as mock_print:
                with pytest.raises(SystemExit) as exc_info:
                    main()
        
        # Should still exit successfully after handling interrupt
        assert exc_info.value.code == 0
        
        # Verify interrupt message was printed
        print_calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        interrupt_messages = [msg for msg in print_calls if "interrupted" in msg.lower()]
        assert len(interrupt_messages) > 0
    
    def test_progress_reporting_integration(self):
        """Test progress reporting during batch processing."""
        # Create many mock MP3 files to trigger progress reporting
        mp3_files = self.create_mock_mp3_files(15)  # More than 10 to trigger progress
        
        test_args = [
            'mp3_id3_processor',
            '--directory', str(self.music_dir),
            '--verbose',
            '--dry-run'
        ]
        
        with patch('mp3_id3_processor.main.FileScanner') as mock_scanner_class:
            with patch('mp3_id3_processor.main.ID3Processor') as mock_processor_class:
                # Setup mocks
                mock_scanner = Mock()
                mock_scanner.scan_directory.return_value = mp3_files
                mock_scanner_class.return_value = mock_scanner
                
                mock_processor = Mock()
                mock_processor.process_file.return_value = ProcessingResult(mp3_files[0], True, [])
                mock_processor_class.return_value = mock_processor
                
                with patch('sys.argv', test_args):
                    with patch('builtins.print') as mock_print:
                        with pytest.raises(SystemExit) as exc_info:
                            main()
                
                assert exc_info.value.code == 0
                
                # Verify progress messages were printed (verbose mode with >10 files)
                print_calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
                progress_messages = [msg for msg in print_calls if "Progress:" in msg]
                # Should have progress messages since we have >10 files and verbose mode
                assert len(progress_messages) > 0


class TestComponentIntegration:
    """Test integration between individual components."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.music_dir = self.temp_dir / "music"
        self.music_dir.mkdir()
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_config_scanner_integration(self):
        """Test integration between Configuration and FileScanner."""
        # Create configuration
        config = Configuration()
        config.update_from_dict({'music_directory': str(self.music_dir)})
        
        # Create test MP3 file
        test_mp3 = self.music_dir / "test.mp3"
        test_mp3.write_bytes(b"fake mp3")
        
        # Test scanner with config directory
        scanner = FileScanner()
        files = scanner.scan_directory(config.music_directory)
        
        assert len(files) == 1
        assert files[0].name == "test.mp3"
    
    def test_config_processor_integration(self):
        """Test integration between Configuration and ID3Processor."""
        # Create configuration with custom values
        config = Configuration()
        config.update_from_dict({
            'default_genre': 'TestGenre',
            'default_year': '2023'
        })
        
        # Create processor with config
        processor = ID3Processor(config)
        
        # Verify processor uses config values
        assert processor.config.default_genre == 'TestGenre'
        assert processor.config.default_year == '2023'
    
    def test_logger_results_integration(self):
        """Test integration between ProcessingLogger and ProcessingResults."""
        logger = ProcessingLogger(verbose=True)
        
        # Create test results
        results = ProcessingResults(total_files=3)
        results.add_result(ProcessingResult(Path("test1.mp3"), True, ["genre"]))
        results.add_result(ProcessingResult(Path("test2.mp3"), True, []))
        results.add_result(ProcessingResult(Path("test3.mp3"), False, [], "Error"))
        
        # Test logger can handle results
        with patch('builtins.print') as mock_print:
            logger.log_summary(results)
        
        # Verify summary was printed
        mock_print.assert_called()
        
        # Check that summary contains expected information
        print_calls = [str(call) for call in mock_print.call_args_list]
        summary_text = " ".join(print_calls)
        assert "Total files found: 3" in summary_text
        assert "Files modified: 1" in summary_text
        assert "Errors encountered: 1" in summary_text


class TestErrorRecoveryIntegration:
    """Test error recovery and resilience in integrated workflows."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.music_dir = self.temp_dir / "music"
        self.music_dir.mkdir()
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('mp3_id3_processor.main.FileScanner')
    @patch('mp3_id3_processor.main.ID3Processor')
    def test_partial_failure_recovery(self, mock_processor_class, mock_scanner_class):
        """Test that the application continues processing after individual file failures."""
        # Create mock files
        mp3_files = [
            Path("song1.mp3"),
            Path("song2.mp3"),
            Path("song3.mp3")
        ]
        
        # Setup scanner
        mock_scanner = Mock()
        mock_scanner.scan_directory.return_value = mp3_files
        mock_scanner_class.return_value = mock_scanner
        
        # Setup processor with mixed results including exceptions
        mock_processor = Mock()
        def process_side_effect(file_path):
            if file_path.name == "song1.mp3":
                return ProcessingResult(file_path, True, ["genre"])
            elif file_path.name == "song2.mp3":
                raise Exception("Unexpected processing error")
            else:
                return ProcessingResult(file_path, True, ["year"])
        
        mock_processor.process_file.side_effect = process_side_effect
        mock_processor_class.return_value = mock_processor
        
        test_args = [
            'mp3_id3_processor',
            '--directory', str(self.music_dir)
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
        
        # Should exit with partial success code
        assert exc_info.value.code == 2
        
        # Verify all files were attempted despite the exception
        assert mock_processor.process_file.call_count == 3
    
    def test_configuration_validation_integration(self):
        """Test configuration validation in integrated workflow."""
        # Create invalid configuration file
        config_file = self.temp_dir / "invalid_config.json"
        with open(config_file, 'w') as f:
            f.write("invalid json content")
        
        test_args = [
            'mp3_id3_processor',
            '--directory', str(self.music_dir),
            '--config', str(config_file)
        ]
        
        with patch('sys.argv', test_args):
            with patch('builtins.print') as mock_print:
                with pytest.raises(SystemExit) as exc_info:
                    main()
        
        # Should handle invalid config gracefully and continue with defaults
        # The application should still try to process (though it will find no files)
        assert exc_info.value.code == 0  # No files found, but not an error