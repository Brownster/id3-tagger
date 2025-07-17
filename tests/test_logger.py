"""Unit tests for the ProcessingLogger class."""

import pytest
from io import StringIO
import sys
from pathlib import Path
from unittest.mock import patch

from mp3_id3_processor.logger import ProcessingLogger
from mp3_id3_processor.models import ProcessingResults, ProcessingResult


class TestProcessingLogger:
    """Test cases for ProcessingLogger class."""
    
    def test_init_default(self):
        """Test logger initialization with default settings."""
        logger = ProcessingLogger()
        assert logger.verbose is False
        assert logger._files_processed == 0
        assert logger._total_files == 0
    
    def test_init_verbose(self):
        """Test logger initialization with verbose mode enabled."""
        logger = ProcessingLogger(verbose=True)
        assert logger.verbose is True
        assert logger._files_processed == 0
        assert logger._total_files == 0
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_log_start(self, mock_stdout):
        """Test logging of processing start."""
        logger = ProcessingLogger()
        logger.log_start(10)
        
        output = mock_stdout.getvalue()
        assert "Starting MP3 ID3 tag processing..." in output
        assert "Found 10 MP3 files to process" in output
        assert "-" * 50 in output
        assert logger._total_files == 10
        assert logger._files_processed == 0
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_log_file_processing_with_tags(self, mock_stdout):
        """Test logging of file processing when tags are added."""
        logger = ProcessingLogger()
        logger._total_files = 5
        
        file_path = Path("/test/music/song.mp3")
        tags_added = ["genre", "year"]
        
        logger.log_file_processing(file_path, tags_added)
        
        output = mock_stdout.getvalue()
        assert "[1/5]" in output
        assert "song.mp3" in output
        assert "Added genre, year" in output
        assert logger._files_processed == 1
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_log_file_processing_no_tags_verbose(self, mock_stdout):
        """Test logging of file processing when no tags are added (verbose mode)."""
        logger = ProcessingLogger(verbose=True)
        logger._total_files = 3
        
        file_path = Path("/test/music/song.mp3")
        tags_added = []
        
        logger.log_file_processing(file_path, tags_added)
        
        output = mock_stdout.getvalue()
        assert "[1/3]" in output
        assert "song.mp3" in output
        assert "No changes needed" in output
        assert logger._files_processed == 1
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_log_file_processing_no_tags_not_verbose(self, mock_stdout):
        """Test logging of file processing when no tags are added (non-verbose mode)."""
        logger = ProcessingLogger(verbose=False)
        logger._total_files = 3
        
        file_path = Path("/test/music/song.mp3")
        tags_added = []
        
        logger.log_file_processing(file_path, tags_added)
        
        output = mock_stdout.getvalue()
        # Should not log anything in non-verbose mode when no tags added
        assert output == ""
        assert logger._files_processed == 1
    
    @patch('sys.stderr', new_callable=StringIO)
    def test_log_error(self, mock_stderr):
        """Test logging of processing errors."""
        logger = ProcessingLogger()
        logger._total_files = 5
        
        file_path = Path("/test/music/corrupted.mp3")
        error = Exception("File is corrupted")
        
        logger.log_error(file_path, error)
        
        output = mock_stderr.getvalue()
        assert "[1/5]" in output
        assert "ERROR processing corrupted.mp3" in output
        assert "File is corrupted" in output
        assert logger._files_processed == 1
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_log_summary_successful_processing(self, mock_stdout):
        """Test logging of summary with successful processing results."""
        logger = ProcessingLogger()
        
        # Create test results
        results = ProcessingResults(total_files=10)
        results.processed_files = 10
        results.files_modified = 7
        results.tags_added_count = {"genre": 5, "year": 4}
        
        logger.log_summary(results)
        
        output = mock_stdout.getvalue()
        assert "PROCESSING SUMMARY" in output
        assert "Total files found: 10" in output
        assert "Files processed: 10" in output
        assert "Files modified: 7" in output
        assert "Success rate: 100.0%" in output
        assert "Tags added:" in output
        assert "genre: 5 files" in output
        assert "year: 4 files" in output
        assert "No errors encountered" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_log_summary_with_errors(self, mock_stdout):
        """Test logging of summary with errors."""
        logger = ProcessingLogger(verbose=True)
        
        # Create test results with errors
        results = ProcessingResults(total_files=5)
        results.processed_files = 4
        results.files_modified = 3
        results.tags_added_count = {"genre": 2}
        
        # Add error results
        error_result = ProcessingResult(
            file_path=Path("/test/error.mp3"),
            success=False,
            error_message="Permission denied"
        )
        results.errors.append(error_result)
        
        logger.log_summary(results)
        
        output = mock_stdout.getvalue()
        assert "Total files found: 5" in output
        assert "Files processed: 4" in output
        assert "Files modified: 3" in output
        assert "Success rate: 60.0%" in output
        assert "Errors encountered: 1" in output
        assert "Error details:" in output
        assert "error.mp3: Permission denied" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_log_summary_no_tags_added(self, mock_stdout):
        """Test logging of summary when no tags were added."""
        logger = ProcessingLogger()
        
        results = ProcessingResults(total_files=5)
        results.processed_files = 5
        results.files_modified = 0
        results.tags_added_count = {}
        
        logger.log_summary(results)
        
        output = mock_stdout.getvalue()
        assert "No tags were added (all files already had required tags)" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_log_progress_update_verbose(self, mock_stdout):
        """Test progress update logging in verbose mode."""
        logger = ProcessingLogger(verbose=True)
        
        logger.log_progress_update(3, 10, "song.mp3")
        
        output = mock_stdout.getvalue()
        assert "Progress: 3/10 (30.0%)" in output
        assert "Processing: song.mp3" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_log_progress_update_not_verbose(self, mock_stdout):
        """Test progress update logging in non-verbose mode."""
        logger = ProcessingLogger(verbose=False)
        
        logger.log_progress_update(3, 10, "song.mp3")
        
        output = mock_stdout.getvalue()
        assert output == ""  # Should not log in non-verbose mode
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_log_progress_update_no_filename(self, mock_stdout):
        """Test progress update logging without filename."""
        logger = ProcessingLogger(verbose=True)
        
        logger.log_progress_update(5, 10)
        
        output = mock_stdout.getvalue()
        assert "Progress: 5/10 (50.0%)" in output
        assert "Processing:" not in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_log_info_verbose(self, mock_stdout):
        """Test info logging in verbose mode."""
        logger = ProcessingLogger(verbose=True)
        
        logger.log_info("Test info message")
        
        output = mock_stdout.getvalue()
        assert "INFO: Test info message" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_log_info_not_verbose(self, mock_stdout):
        """Test info logging in non-verbose mode."""
        logger = ProcessingLogger(verbose=False)
        
        logger.log_info("Test info message")
        
        output = mock_stdout.getvalue()
        assert output == ""  # Should not log in non-verbose mode
    
    @patch('sys.stderr', new_callable=StringIO)
    def test_log_warning(self, mock_stderr):
        """Test warning logging."""
        logger = ProcessingLogger()
        
        logger.log_warning("Test warning message")
        
        output = mock_stderr.getvalue()
        assert "WARNING: Test warning message" in output
    
    def test_progress_tracking(self):
        """Test that progress tracking works correctly."""
        logger = ProcessingLogger()
        logger.log_start(5)
        
        assert logger._total_files == 5
        assert logger._files_processed == 0
        
        # Simulate processing files
        logger.log_file_processing(Path("file1.mp3"), ["genre"])
        assert logger._files_processed == 1
        
        logger.log_error(Path("file2.mp3"), Exception("Error"))
        assert logger._files_processed == 2
        
        logger.log_file_processing(Path("file3.mp3"), [])
        assert logger._files_processed == 3
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_summary_statistics_calculation(self, mock_stdout):
        """Test that summary statistics are calculated and displayed correctly."""
        logger = ProcessingLogger()
        
        # Create comprehensive test results
        results = ProcessingResults(total_files=20)
        results.processed_files = 18
        results.files_modified = 12
        results.tags_added_count = {"genre": 8, "year": 7, "album": 3}
        
        # Add multiple error results
        for i in range(2):
            error_result = ProcessingResult(
                file_path=Path(f"/test/error{i}.mp3"),
                success=False,
                error_message=f"Error {i}"
            )
            results.errors.append(error_result)
        
        logger.log_summary(results)
        
        output = mock_stdout.getvalue()
        
        # Verify all statistics are displayed
        assert "Total files found: 20" in output
        assert "Files processed: 18" in output
        assert "Files modified: 12" in output
        assert "Success rate: 80.0%" in output  # (18-2)/20 * 100 = 80%
        
        # Verify tag statistics
        assert "genre: 8 files" in output
        assert "year: 7 files" in output
        assert "album: 3 files" in output
        
        # Verify error reporting
        assert "Errors encountered: 2" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_summary_formatting_edge_cases(self, mock_stdout):
        """Test summary formatting with edge cases."""
        logger = ProcessingLogger()
        
        # Test with zero files
        results = ProcessingResults(total_files=0)
        logger.log_summary(results)
        
        output = mock_stdout.getvalue()
        assert "Total files found: 0" in output
        assert "Success rate: 0.0%" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_detailed_error_reporting_verbose(self, mock_stdout):
        """Test detailed error reporting in verbose mode."""
        logger = ProcessingLogger(verbose=True)
        
        results = ProcessingResults(total_files=5)
        results.processed_files = 3
        
        # Add various types of errors
        error_types = [
            ("corrupted.mp3", "File is corrupted"),
            ("permission.mp3", "Permission denied"),
            ("invalid.mp3", "Invalid MP3 format")
        ]
        
        for filename, error_msg in error_types:
            error_result = ProcessingResult(
                file_path=Path(f"/test/{filename}"),
                success=False,
                error_message=error_msg
            )
            results.errors.append(error_result)
        
        logger.log_summary(results)
        
        output = mock_stdout.getvalue()
        
        # Verify detailed error reporting
        assert "Error details:" in output
        assert "corrupted.mp3: File is corrupted" in output
        assert "permission.mp3: Permission denied" in output
        assert "invalid.mp3: Invalid MP3 format" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_detailed_error_reporting_not_verbose(self, mock_stdout):
        """Test error reporting in non-verbose mode (should show count but not details)."""
        logger = ProcessingLogger(verbose=False)
        
        results = ProcessingResults(total_files=5)
        results.processed_files = 3
        
        error_result = ProcessingResult(
            file_path=Path("/test/error.mp3"),
            success=False,
            error_message="Some error"
        )
        results.errors.append(error_result)
        
        logger.log_summary(results)
        
        output = mock_stdout.getvalue()
        
        # Should show error count but not details
        assert "Errors encountered: 1" in output
        assert "Error details:" not in output
        assert "error.mp3: Some error" not in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_summary_display_formatting(self, mock_stdout):
        """Test that summary display formatting is consistent and readable."""
        logger = ProcessingLogger()
        
        results = ProcessingResults(total_files=100)
        results.processed_files = 95
        results.files_modified = 50
        results.tags_added_count = {"genre": 30, "year": 25}
        
        logger.log_summary(results)
        
        output = mock_stdout.getvalue()
        
        # Verify formatting elements
        assert "=" * 50 in output  # Header separator
        assert "PROCESSING SUMMARY" in output
        assert output.count("=" * 50) >= 2  # Header and footer separators
        
        # Verify sections are properly separated
        lines = output.split('\n')
        summary_line = next(i for i, line in enumerate(lines) if "PROCESSING SUMMARY" in line)
        assert "=" in lines[summary_line - 1]  # Line before summary
        assert "=" in lines[summary_line + 1]  # Line after summary