"""Unit tests for the FileScanner class."""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from mp3_id3_processor.scanner import FileScanner


class TestFileScanner:
    """Test cases for FileScanner class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scanner = FileScanner()
    
    def test_init(self):
        """Test FileScanner initialization."""
        scanner = FileScanner()
        assert scanner is not None
    
    def test_is_mp3_file_valid_extension(self):
        """Test is_mp3_file with valid MP3 extension."""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp_path = Path(tmp.name)
            try:
                assert self.scanner.is_mp3_file(tmp_path) is True
            finally:
                tmp_path.unlink()
    
    def test_is_mp3_file_case_insensitive(self):
        """Test is_mp3_file with different case extensions."""
        with tempfile.NamedTemporaryFile(suffix='.MP3', delete=False) as tmp:
            tmp_path = Path(tmp.name)
            try:
                assert self.scanner.is_mp3_file(tmp_path) is True
            finally:
                tmp_path.unlink()
        
        with tempfile.NamedTemporaryFile(suffix='.Mp3', delete=False) as tmp:
            tmp_path = Path(tmp.name)
            try:
                assert self.scanner.is_mp3_file(tmp_path) is True
            finally:
                tmp_path.unlink()
    
    def test_is_mp3_file_invalid_extension(self):
        """Test is_mp3_file with invalid extensions."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp_path = Path(tmp.name)
            try:
                assert self.scanner.is_mp3_file(tmp_path) is False
            finally:
                tmp_path.unlink()
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = Path(tmp.name)
            try:
                assert self.scanner.is_mp3_file(tmp_path) is False
            finally:
                tmp_path.unlink()
    
    def test_is_mp3_file_nonexistent_file(self):
        """Test is_mp3_file with nonexistent file."""
        nonexistent_path = Path("/nonexistent/file.mp3")
        assert self.scanner.is_mp3_file(nonexistent_path) is False
    
    def test_is_mp3_file_directory(self):
        """Test is_mp3_file with directory path."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            assert self.scanner.is_mp3_file(dir_path) is False
    
    def test_is_accessible_readable_writable_file(self):
        """Test is_accessible with readable and writable file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            try:
                # Ensure file is readable and writable
                os.chmod(tmp_path, 0o666)
                assert self.scanner.is_accessible(tmp_path) is True
            finally:
                tmp_path.unlink()
    
    def test_is_accessible_nonexistent_file(self):
        """Test is_accessible with nonexistent file."""
        nonexistent_path = Path("/nonexistent/file.mp3")
        assert self.scanner.is_accessible(nonexistent_path) is False
    
    def test_is_accessible_directory(self):
        """Test is_accessible with directory path."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            assert self.scanner.is_accessible(dir_path) is False
    
    @patch('os.access')
    def test_is_accessible_permission_denied(self, mock_access):
        """Test is_accessible when file permissions are denied."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            try:
                # Mock os.access to return False (no read/write permission)
                mock_access.return_value = False
                assert self.scanner.is_accessible(tmp_path) is False
            finally:
                tmp_path.unlink()
    
    def test_scan_directory_nonexistent(self):
        """Test scan_directory with nonexistent directory."""
        nonexistent_dir = Path("/nonexistent/directory")
        with pytest.raises(FileNotFoundError, match="Directory does not exist"):
            self.scanner.scan_directory(nonexistent_dir)
    
    def test_scan_directory_not_a_directory(self):
        """Test scan_directory with file path instead of directory."""
        with tempfile.NamedTemporaryFile() as tmp:
            file_path = Path(tmp.name)
            with pytest.raises(NotADirectoryError, match="Path is not a directory"):
                self.scanner.scan_directory(file_path)
    
    @patch('os.access')
    def test_scan_directory_permission_denied(self, mock_access):
        """Test scan_directory with directory that can't be read."""
        from mp3_id3_processor.scanner import DirectoryAccessError
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            # Mock os.access to return False for read permission
            mock_access.return_value = False
            with pytest.raises(DirectoryAccessError, match="Directory is not accessible"):
                self.scanner.scan_directory(dir_path)
    
    def test_scan_directory_empty(self):
        """Test scan_directory with empty directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            result = self.scanner.scan_directory(dir_path)
            assert result == []
    
    def test_scan_directory_with_mp3_files(self):
        """Test scan_directory with MP3 files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            
            # Create test MP3 files
            mp3_file1 = dir_path / "song1.mp3"
            mp3_file2 = dir_path / "song2.MP3"
            txt_file = dir_path / "readme.txt"
            
            mp3_file1.touch()
            mp3_file2.touch()
            txt_file.touch()
            
            result = self.scanner.scan_directory(dir_path)
            
            # Should find both MP3 files but not the txt file
            assert len(result) == 2
            assert mp3_file1 in result
            assert mp3_file2 in result
            assert txt_file not in result
    
    def test_scan_directory_recursive(self):
        """Test scan_directory recursively finds files in subdirectories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            
            # Create subdirectory structure
            subdir1 = dir_path / "subdir1"
            subdir2 = dir_path / "subdir1" / "subdir2"
            subdir1.mkdir()
            subdir2.mkdir()
            
            # Create MP3 files in different levels
            mp3_root = dir_path / "root.mp3"
            mp3_sub1 = subdir1 / "sub1.mp3"
            mp3_sub2 = subdir2 / "sub2.mp3"
            
            mp3_root.touch()
            mp3_sub1.touch()
            mp3_sub2.touch()
            
            result = self.scanner.scan_directory(dir_path)
            
            # Should find all MP3 files recursively
            assert len(result) == 3
            assert mp3_root in result
            assert mp3_sub1 in result
            assert mp3_sub2 in result
    
    @patch('os.access')
    def test_scan_directory_skips_inaccessible_subdirs(self, mock_access):
        """Test scan_directory skips subdirectories without read permission."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            
            # Create subdirectory
            subdir = dir_path / "subdir"
            subdir.mkdir()
            
            # Create MP3 files
            mp3_root = dir_path / "root.mp3"
            mp3_sub = subdir / "sub.mp3"
            mp3_root.touch()
            mp3_sub.touch()
            
            # Mock os.access to deny access to subdirectory
            def mock_access_func(path, mode):
                if Path(path) == subdir:
                    return False
                return True
            
            mock_access.side_effect = mock_access_func
            
            result = self.scanner.scan_directory(dir_path)
            
            # Should only find root MP3 file, not the one in inaccessible subdir
            assert len(result) == 1
            assert mp3_root in result
            assert mp3_sub not in result
    
    @patch('mp3_id3_processor.scanner.logger')
    def test_scan_directory_logs_found_files(self, mock_logger):
        """Test scan_directory logs found MP3 files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            
            # Create test MP3 file
            mp3_file = dir_path / "test.mp3"
            mp3_file.touch()
            
            self.scanner.scan_directory(dir_path)
            
            # Verify logging calls
            mock_logger.debug.assert_called()
            mock_logger.info.assert_called_with(f"Found 1 MP3 files in {dir_path}")
    
    def test_scanner_error_exceptions(self):
        """Test custom scanner exception classes."""
        from mp3_id3_processor.scanner import ScannerError, DirectoryAccessError, FileAccessError
        
        # Test base exception
        with pytest.raises(ScannerError):
            raise ScannerError("Test error")
        
        # Test directory access error
        with pytest.raises(DirectoryAccessError):
            raise DirectoryAccessError("Directory access error")
        
        # Test file access error
        with pytest.raises(FileAccessError):
            raise FileAccessError("File access error")
        
        # Test inheritance
        assert issubclass(DirectoryAccessError, ScannerError)
        assert issubclass(FileAccessError, ScannerError)
    
    @patch('os.access')
    def test_validate_directory_not_accessible(self, mock_access):
        """Test _validate_directory with inaccessible directory."""
        from mp3_id3_processor.scanner import DirectoryAccessError
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            
            # Mock os.access to return False (no read/execute permission)
            mock_access.return_value = False
            
            with pytest.raises(DirectoryAccessError, match="Directory is not accessible"):
                self.scanner._validate_directory(dir_path)
    
    def test_validate_directory_success(self):
        """Test _validate_directory with valid directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            
            # Should not raise any exception
            self.scanner._validate_directory(dir_path)
    
    def test_is_directory_accessible_success(self):
        """Test _is_directory_accessible with accessible directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            assert self.scanner._is_directory_accessible(dir_path) is True
    
    @patch('os.access')
    def test_is_directory_accessible_denied(self, mock_access):
        """Test _is_directory_accessible with permission denied."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            
            # Mock os.access to return False
            mock_access.return_value = False
            assert self.scanner._is_directory_accessible(dir_path) is False
    
    @patch('os.access')
    def test_is_directory_accessible_exception(self, mock_access):
        """Test _is_directory_accessible handles exceptions gracefully."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            
            # Mock os.access to raise an exception
            mock_access.side_effect = OSError("Mock OS error")
            assert self.scanner._is_directory_accessible(dir_path) is False
    
    @patch('os.walk')
    def test_scan_directory_os_error(self, mock_walk):
        """Test scan_directory handles OS errors."""
        from mp3_id3_processor.scanner import ScannerError
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            
            # Mock os.walk to raise OSError
            mock_walk.side_effect = OSError("Mock OS error")
            
            with pytest.raises(ScannerError, match="OS error while scanning"):
                self.scanner.scan_directory(dir_path)
    
    @patch('os.walk')
    def test_scan_directory_permission_error(self, mock_walk):
        """Test scan_directory handles permission errors."""
        from mp3_id3_processor.scanner import DirectoryAccessError
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            
            # Mock os.walk to raise PermissionError
            mock_walk.side_effect = PermissionError("Mock permission error")
            
            with pytest.raises(DirectoryAccessError, match="Permission denied while scanning"):
                self.scanner.scan_directory(dir_path)
    
    @patch('os.walk')
    def test_scan_directory_unexpected_error(self, mock_walk):
        """Test scan_directory handles unexpected errors."""
        from mp3_id3_processor.scanner import ScannerError
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            
            # Mock os.walk to raise unexpected exception
            mock_walk.side_effect = ValueError("Mock unexpected error")
            
            with pytest.raises(ScannerError, match="Unexpected error while scanning"):
                self.scanner.scan_directory(dir_path)
    
    @patch('mp3_id3_processor.scanner.logger')
    def test_scan_directory_logs_inaccessible_subdirs(self, mock_logger):
        """Test scan_directory logs warnings for inaccessible subdirectories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            
            # Create subdirectory
            subdir = dir_path / "subdir"
            subdir.mkdir()
            
            # Create MP3 file in root
            mp3_file = dir_path / "test.mp3"
            mp3_file.touch()
            
            # Mock _is_directory_accessible to return False for subdir
            with patch.object(self.scanner, '_is_directory_accessible') as mock_accessible:
                def mock_accessible_func(path):
                    return path != subdir
                mock_accessible.side_effect = mock_accessible_func
                
                result = self.scanner.scan_directory(dir_path)
                
                # Should find the MP3 file in root
                assert len(result) == 1
                assert mp3_file in result
                
                # Should log warning about inaccessible subdirectory
                mock_logger.warning.assert_any_call(f"Skipping inaccessible directory: {subdir}")
    
    @patch('mp3_id3_processor.scanner.logger')
    def test_scan_directory_logs_inaccessible_mp3_files(self, mock_logger):
        """Test scan_directory logs warnings for inaccessible MP3 files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            
            # Create MP3 files
            mp3_file1 = dir_path / "accessible.mp3"
            mp3_file2 = dir_path / "inaccessible.mp3"
            mp3_file1.touch()
            mp3_file2.touch()
            
            # Mock is_accessible to return False for mp3_file2
            with patch.object(self.scanner, 'is_accessible') as mock_accessible:
                def mock_accessible_func(path):
                    return path != mp3_file2
                mock_accessible.side_effect = mock_accessible_func
                
                result = self.scanner.scan_directory(dir_path)
                
                # Should only find the accessible MP3 file
                assert len(result) == 1
                assert mp3_file1 in result
                assert mp3_file2 not in result
                
                # Should log warning about inaccessible MP3 file
                mock_logger.warning.assert_any_call(f"MP3 file not accessible: {mp3_file2}")
    
    @patch('mp3_id3_processor.scanner.logger')
    def test_scan_directory_handles_file_processing_errors(self, mock_logger):
        """Test scan_directory handles errors during file processing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            
            # Create MP3 file
            mp3_file = dir_path / "test.mp3"
            mp3_file.touch()
            
            # Mock is_mp3_file to raise an exception
            with patch.object(self.scanner, 'is_mp3_file') as mock_is_mp3:
                mock_is_mp3.side_effect = Exception("Mock file processing error")
                
                result = self.scanner.scan_directory(dir_path)
                
                # Should return empty list due to error
                assert len(result) == 0
                
                # Should log warning about file processing error
                mock_logger.warning.assert_any_call(f"Error processing file {mp3_file}: Mock file processing error")
    
    @patch('mp3_id3_processor.scanner.logger')
    def test_scan_directory_logs_error_summary(self, mock_logger):
        """Test scan_directory logs summary of errors encountered."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            
            # Create subdirectory and MP3 file
            subdir = dir_path / "subdir"
            subdir.mkdir()
            mp3_file = dir_path / "test.mp3"
            mp3_file.touch()
            
            # Mock methods to simulate errors, but allow main directory to be accessible
            with patch.object(self.scanner, '_is_directory_accessible') as mock_dir_accessible, \
                 patch.object(self.scanner, 'is_accessible', return_value=False) as mock_file_accessible:
                
                # Allow main directory to be accessible, but not subdirectory
                def mock_dir_accessible_func(path):
                    return path == dir_path  # Only main directory is accessible
                mock_dir_accessible.side_effect = mock_dir_accessible_func
                
                result = self.scanner.scan_directory(dir_path)
                
                # Should return empty list due to inaccessible file
                assert len(result) == 0
                
                # Should log error summary
                mock_logger.warning.assert_any_call("Encountered 2 errors during scan")
    
    def test_validate_directory_with_exception_handling(self):
        """Test _validate_directory handles unexpected exceptions."""
        from mp3_id3_processor.scanner import ScannerError
        
        # Create a mock Path object that raises an exception
        mock_path = MagicMock()
        mock_path.exists.side_effect = Exception("Mock validation error")
        
        with pytest.raises(ScannerError, match="Error validating directory"):
            self.scanner._validate_directory(mock_path)
    
    def test_scan_directory_with_mixed_file_types_and_errors(self):
        """Test scan_directory with mixed file types and various error conditions."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            
            # Create various file types
            mp3_file = dir_path / "song.mp3"
            txt_file = dir_path / "readme.txt"
            wav_file = dir_path / "audio.wav"
            
            mp3_file.touch()
            txt_file.touch()
            wav_file.touch()
            
            # Create subdirectory with MP3 file
            subdir = dir_path / "subdir"
            subdir.mkdir()
            sub_mp3 = subdir / "subsong.mp3"
            sub_mp3.touch()
            
            result = self.scanner.scan_directory(dir_path)
            
            # Should find both MP3 files but not other file types
            assert len(result) == 2
            assert mp3_file in result
            assert sub_mp3 in result
            assert txt_file not in result
            assert wav_file not in result