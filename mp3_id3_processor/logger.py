"""Logger module for progress and error reporting."""

import sys
from pathlib import Path
from typing import List, Optional
from .models import ProcessingResults, ProcessingResult


class ProcessingLogger:
    """Logger for MP3 ID3 processing operations with progress and error reporting."""
    
    def __init__(self, verbose: bool = False):
        """Initialize the logger with optional verbose mode.
        
        Args:
            verbose: Enable verbose logging output
        """
        self.verbose = verbose
        self._files_processed = 0
        self._total_files = 0
    
    def log_start(self, total_files: int):
        """Log the start of processing with total file count.
        
        Args:
            total_files: Total number of files to process
        """
        self._total_files = total_files
        self._files_processed = 0
        
        print(f"Starting MP3 ID3 tag processing...")
        print(f"Found {total_files} MP3 files to process")
        print("-" * 50)
    
    def log_file_processing(self, file_path: Path, tags_added: List[str]):
        """Log the processing of an individual file.
        
        Args:
            file_path: Path to the file being processed
            tags_added: List of tags that were added to the file
        """
        self._files_processed += 1
        
        # Show progress
        progress = f"[{self._files_processed}/{self._total_files}]"
        
        if tags_added:
            tags_str = ", ".join(tags_added)
            print(f"{progress} {file_path.name}: Added {tags_str}")
        else:
            if self.verbose:
                print(f"{progress} {file_path.name}: No changes needed")
    
    def log_error(self, file_path: Path, error: Exception):
        """Log an error that occurred during file processing.
        
        Args:
            file_path: Path to the file that caused the error
            error: The exception that occurred
        """
        self._files_processed += 1
        
        progress = f"[{self._files_processed}/{self._total_files}]"
        print(f"{progress} ERROR processing {file_path.name}: {str(error)}", file=sys.stderr)
    
    def log_summary(self, results: ProcessingResults):
        """Log a comprehensive summary of processing results.
        
        Args:
            results: ProcessingResults containing all processing statistics
        """
        print("\n" + "=" * 50)
        print("PROCESSING SUMMARY")
        print("=" * 50)
        
        # Basic statistics
        print(f"Total files found: {results.total_files}")
        print(f"Files processed: {results.processed_files}")
        print(f"Files modified: {results.files_modified}")
        print(f"Success rate: {results.success_rate:.1f}%")
        
        # Tag addition statistics
        if results.tags_added_count:
            print(f"\nTags added:")
            for tag, count in results.tags_added_count.items():
                print(f"  {tag}: {count} files")
        else:
            print(f"\nNo tags were added (all files already had required tags)")
        
        # Error reporting
        if results.errors:
            print(f"\nErrors encountered: {results.error_count}")
            if self.verbose:
                print("Error details:")
                for error_result in results.errors:
                    print(f"  {error_result.file_path.name}: {error_result.error_message}")
        else:
            print(f"\nNo errors encountered")
        
        print("=" * 50)
    
    def log_progress_update(self, current: int, total: int, file_name: Optional[str] = None):
        """Log a progress update during processing.
        
        Args:
            current: Current number of files processed
            total: Total number of files to process
            file_name: Optional name of current file being processed
        """
        if self.verbose:
            percentage = (current / total * 100) if total > 0 else 0
            if file_name:
                print(f"Progress: {current}/{total} ({percentage:.1f}%) - Processing: {file_name}")
            else:
                print(f"Progress: {current}/{total} ({percentage:.1f}%)")
    
    def log_info(self, message: str):
        """Log an informational message.
        
        Args:
            message: The message to log
        """
        if self.verbose:
            print(f"INFO: {message}")
    
    def log_warning(self, message: str):
        """Log a warning message.
        
        Args:
            message: The warning message to log
        """
        print(f"WARNING: {message}", file=sys.stderr)