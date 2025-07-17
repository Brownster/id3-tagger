"""File scanner module for discovering MP3 files."""

import os
from pathlib import Path
from typing import List
import logging

logger = logging.getLogger(__name__)


class ScannerError(Exception):
    """Base exception for scanner-related errors."""
    pass


class DirectoryAccessError(ScannerError):
    """Raised when directory cannot be accessed."""
    pass


class FileAccessError(ScannerError):
    """Raised when file cannot be accessed."""
    pass


class FileScanner:
    """Scans directories for MP3 files and validates their accessibility."""
    
    def __init__(self):
        """Initialize the FileScanner."""
        pass
    
    def scan_directory(self, directory: Path) -> List[Path]:
        """
        Scan directory recursively for MP3 files.
        
        Args:
            directory: Path to the directory to scan
            
        Returns:
            List of Path objects for accessible MP3 files
            
        Raises:
            FileNotFoundError: If the directory doesn't exist
            NotADirectoryError: If the path is not a directory
            DirectoryAccessError: If the directory cannot be accessed
            ScannerError: For other scanning-related errors
        """
        # Validate directory existence and accessibility
        self._validate_directory(directory)
        
        mp3_files = []
        scan_errors = []
        
        try:
            # Recursively walk through the directory
            for root, dirs, files in os.walk(directory):
                root_path = Path(root)
                
                # Filter out inaccessible directories and log warnings
                accessible_dirs = []
                for d in dirs:
                    dir_path = root_path / d
                    if self._is_directory_accessible(dir_path):
                        accessible_dirs.append(d)
                    else:
                        logger.warning(f"Skipping inaccessible directory: {dir_path}")
                        scan_errors.append(f"Cannot access directory: {dir_path}")
                
                dirs[:] = accessible_dirs
                
                # Process files in current directory
                for file in files:
                    file_path = root_path / file
                    
                    try:
                        if self.is_mp3_file(file_path):
                            if self.is_accessible(file_path):
                                mp3_files.append(file_path)
                                logger.debug(f"Found MP3 file: {file_path}")
                            else:
                                logger.warning(f"MP3 file not accessible: {file_path}")
                                scan_errors.append(f"Cannot access MP3 file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Error processing file {file_path}: {e}")
                        scan_errors.append(f"Error processing {file_path}: {str(e)}")
        
        except PermissionError as e:
            error_msg = f"Permission denied while scanning {directory}: {e}"
            logger.error(error_msg)
            raise DirectoryAccessError(error_msg) from e
        except OSError as e:
            error_msg = f"OS error while scanning {directory}: {e}"
            logger.error(error_msg)
            raise ScannerError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error while scanning {directory}: {e}"
            logger.error(error_msg)
            raise ScannerError(error_msg) from e
        
        # Log summary
        if scan_errors:
            logger.warning(f"Encountered {len(scan_errors)} errors during scan")
        
        logger.info(f"Found {len(mp3_files)} MP3 files in {directory}")
        return mp3_files
    
    def _validate_directory(self, directory: Path) -> None:
        """
        Validate that the directory exists and is accessible.
        
        Args:
            directory: Path to validate
            
        Raises:
            FileNotFoundError: If the directory doesn't exist
            NotADirectoryError: If the path is not a directory
            DirectoryAccessError: If the directory cannot be accessed
        """
        try:
            if not directory.exists():
                raise FileNotFoundError(f"Directory does not exist: {directory}")
            
            if not directory.is_dir():
                raise NotADirectoryError(f"Path is not a directory: {directory}")
            
            if not self._is_directory_accessible(directory):
                raise DirectoryAccessError(f"Directory is not accessible: {directory}")
                
        except (FileNotFoundError, NotADirectoryError, DirectoryAccessError):
            raise
        except Exception as e:
            error_msg = f"Error validating directory {directory}: {e}"
            logger.error(error_msg)
            raise ScannerError(error_msg) from e
    
    def _is_directory_accessible(self, directory: Path) -> bool:
        """
        Check if directory can be read and executed.
        
        Args:
            directory: Path to check
            
        Returns:
            True if directory is accessible, False otherwise
        """
        try:
            return os.access(directory, os.R_OK | os.X_OK)
        except Exception as e:
            logger.debug(f"Error checking directory accessibility {directory}: {e}")
            return False
    
    def is_mp3_file(self, file_path: Path) -> bool:
        """
        Check if file is a valid MP3 file based on extension.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file appears to be an MP3 file, False otherwise
        """
        if not file_path.is_file():
            return False
        
        # Check file extension (case-insensitive)
        return file_path.suffix.lower() == '.mp3'
    
    def is_accessible(self, file_path: Path) -> bool:
        """
        Check if file can be read and written.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file is readable and writable, False otherwise
        """
        try:
            # Check if file exists and is a regular file
            if not file_path.exists() or not file_path.is_file():
                return False
            
            # Check read and write permissions
            return os.access(file_path, os.R_OK | os.W_OK)
        
        except Exception as e:
            logger.debug(f"Error checking accessibility of {file_path}: {e}")
            return False