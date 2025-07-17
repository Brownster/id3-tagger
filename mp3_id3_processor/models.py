"""Data models for MP3 ID3 processor application."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class ProcessingResult:
    """Result of processing a single MP3 file."""
    file_path: Path
    success: bool
    tags_added: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

    def __post_init__(self):
        """Validate the ProcessingResult after initialization."""
        if not isinstance(self.file_path, Path):
            self.file_path = Path(self.file_path)
        
        if not isinstance(self.success, bool):
            raise ValueError("success must be a boolean")
        
        if not isinstance(self.tags_added, list):
            raise ValueError("tags_added must be a list")
        
        if self.error_message is not None and not isinstance(self.error_message, str):
            raise ValueError("error_message must be a string or None")


@dataclass
class ProcessingResults:
    """Collection of processing results and summary statistics."""
    total_files: int
    processed_files: int = 0
    files_modified: int = 0
    errors: List[ProcessingResult] = field(default_factory=list)
    tags_added_count: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        """Validate the ProcessingResults after initialization."""
        if not isinstance(self.total_files, int) or self.total_files < 0:
            raise ValueError("total_files must be a non-negative integer")
        
        if not isinstance(self.processed_files, int) or self.processed_files < 0:
            raise ValueError("processed_files must be a non-negative integer")
        
        if not isinstance(self.files_modified, int) or self.files_modified < 0:
            raise ValueError("files_modified must be a non-negative integer")
        
        if not isinstance(self.errors, list):
            raise ValueError("errors must be a list")
        
        if not isinstance(self.tags_added_count, dict):
            raise ValueError("tags_added_count must be a dictionary")
        
        # Validate that processed_files doesn't exceed total_files
        if self.processed_files > self.total_files:
            raise ValueError("processed_files cannot exceed total_files")
        
        # Validate that files_modified doesn't exceed processed_files
        if self.files_modified > self.processed_files:
            raise ValueError("files_modified cannot exceed processed_files")

    def add_result(self, result: ProcessingResult):
        """Add a processing result and update statistics."""
        if not isinstance(result, ProcessingResult):
            raise ValueError("result must be a ProcessingResult instance")
        
        self.processed_files += 1
        
        if result.success:
            if result.tags_added:
                self.files_modified += 1
                # Update tag counts
                for tag in result.tags_added:
                    self.tags_added_count[tag] = self.tags_added_count.get(tag, 0) + 1
        else:
            self.errors.append(result)

    @property
    def success_rate(self) -> float:
        """Calculate the success rate as a percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files - len(self.errors)) / self.total_files * 100

    @property
    def error_count(self) -> int:
        """Get the number of errors encountered."""
        return len(self.errors)


@dataclass
class ConfigurationSchema:
    """Configuration schema with validation for application settings."""
    music_directory: str = "~/Music"
    create_backups: bool = False
    verbose: bool = False
    use_api: bool = True
    api_timeout: float = 10.0
    api_cache_dir: Optional[str] = None
    api_request_delay: float = 0.5
    default_genre: str = "Unknown"
    default_year: str = str(datetime.now().year)

    def __post_init__(self):
        """Validate configuration values after initialization."""
        if not isinstance(self.music_directory, str) or not self.music_directory.strip():
            raise ValueError("music_directory must be a non-empty string")
        
        if not isinstance(self.create_backups, bool):
            raise ValueError("create_backups must be a boolean")
        
        if not isinstance(self.verbose, bool):
            raise ValueError("verbose must be a boolean")
        
        if not isinstance(self.use_api, bool):
            raise ValueError("use_api must be a boolean")
        
        if not isinstance(self.api_timeout, (int, float)) or self.api_timeout <= 0:
            raise ValueError("api_timeout must be a positive number")
        
        if self.api_cache_dir is not None and not isinstance(self.api_cache_dir, str):
            raise ValueError("api_cache_dir must be a string or None")
        
        if not isinstance(self.api_request_delay, (int, float)) or self.api_request_delay < 0:
            raise ValueError("api_request_delay must be a non-negative number")
        
        if not isinstance(self.default_genre, str) or not self.default_genre.strip():
            raise ValueError("default_genre must be a non-empty string")
        
        if not isinstance(self.default_year, str) or not self.default_year.strip():
            raise ValueError("default_year must be a non-empty string")

    def get_music_directory_path(self) -> Path:
        """Get the music directory as a Path object with expansion."""
        return Path(self.music_directory).expanduser().resolve()