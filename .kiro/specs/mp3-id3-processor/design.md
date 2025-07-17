# Design Document

## Overview

The MP3 ID3 Processor is a Python-based command-line application that automatically adds missing genre and year ID3 tags to MP3 files in the user's music directory. The application uses the Mutagen library for safe, non-destructive ID3 tag manipulation and provides comprehensive logging and error handling.

## Architecture

The application follows a simple, modular architecture with clear separation of concerns:

```
MP3 ID3 Processor
├── Main Application (CLI Entry Point)
├── File Scanner (Directory Traversal)
├── ID3 Processor (Tag Manipulation)
├── Configuration Manager (Settings)
└── Logger (Progress & Error Reporting)
```

### Key Design Principles

- **Safety First**: All operations are non-destructive and preserve existing metadata
- **Fail-Safe**: Individual file errors don't stop the entire process
- **Transparency**: Clear logging of all operations and results
- **Simplicity**: Single-purpose tool with minimal configuration

## Components and Interfaces

### 1. Main Application (`main.py`)

**Purpose**: CLI entry point and orchestration
**Responsibilities**:
- Parse command-line arguments
- Initialize configuration
- Coordinate file scanning and processing
- Display final summary

**Interface**:
```python
def main():
    """Main entry point for the MP3 ID3 processor"""
    
def parse_arguments() -> argparse.Namespace:
    """Parse and validate command-line arguments"""
    
def display_summary(results: ProcessingResults):
    """Display final processing summary"""
```

### 2. File Scanner (`scanner.py`)

**Purpose**: Discover and validate MP3 files
**Responsibilities**:
- Recursively scan ~/Music directory
- Filter for MP3 files only
- Validate file accessibility
- Return list of processable files

**Interface**:
```python
class FileScanner:
    def scan_directory(self, directory: Path) -> List[Path]:
        """Scan directory for MP3 files"""
        
    def is_mp3_file(self, file_path: Path) -> bool:
        """Check if file is a valid MP3"""
        
    def is_accessible(self, file_path: Path) -> bool:
        """Check if file can be read and written"""
```

### 3. ID3 Processor (`processor.py`)

**Purpose**: Handle ID3 tag manipulation using Mutagen
**Responsibilities**:
- Load MP3 files safely
- Check for missing genre/year tags
- Add missing tags with configured defaults
- Save changes without affecting other metadata

**Interface**:
```python
class ID3Processor:
    def __init__(self, config: Configuration):
        """Initialize with configuration settings"""
        
    def process_file(self, file_path: Path) -> ProcessingResult:
        """Process a single MP3 file"""
        
    def needs_genre_tag(self, audio_file) -> bool:
        """Check if genre tag is missing"""
        
    def needs_year_tag(self, audio_file) -> bool:
        """Check if year tag is missing"""
        
    def add_missing_tags(self, audio_file, file_path: Path) -> List[str]:
        """Add missing genre and year tags"""
```

### 4. Configuration Manager (`config.py`)

**Purpose**: Handle application settings and defaults
**Responsibilities**:
- Load configuration from file or use defaults
- Validate configuration values
- Provide access to settings

**Interface**:
```python
class Configuration:
    def __init__(self, config_file: Optional[Path] = None):
        """Initialize configuration"""
        
    @property
    def default_genre(self) -> str:
        """Get default genre value"""
        
    @property
    def default_year(self) -> str:
        """Get default year value"""
        
    @property
    def music_directory(self) -> Path:
        """Get music directory path"""
```

### 5. Logger (`logger.py`)

**Purpose**: Provide consistent logging and progress reporting
**Responsibilities**:
- Log processing progress
- Report errors and warnings
- Track processing statistics

**Interface**:
```python
class ProcessingLogger:
    def log_start(self, total_files: int):
        """Log processing start"""
        
    def log_file_processing(self, file_path: Path, tags_added: List[str]):
        """Log individual file processing"""
        
    def log_error(self, file_path: Path, error: Exception):
        """Log processing errors"""
        
    def log_summary(self, results: ProcessingResults):
        """Log final summary"""
```

## Data Models

### ProcessingResult
```python
@dataclass
class ProcessingResult:
    file_path: Path
    success: bool
    tags_added: List[str]
    error_message: Optional[str] = None
```

### ProcessingResults
```python
@dataclass
class ProcessingResults:
    total_files: int
    processed_files: int
    files_modified: int
    errors: List[ProcessingResult]
    tags_added_count: Dict[str, int]  # {'genre': 5, 'year': 3}
```

### Configuration Schema
```python
@dataclass
class ConfigurationSchema:
    default_genre: str = "Unknown"
    default_year: str = str(datetime.now().year)
    music_directory: str = "~/Music"
    create_backups: bool = False
    verbose: bool = False
```

## Error Handling

### File-Level Error Handling
- **Corrupted MP3 files**: Skip and log error, continue processing
- **Permission errors**: Skip and log error, continue processing
- **Mutagen parsing errors**: Skip and log error, continue processing

### Application-Level Error Handling
- **Missing ~/Music directory**: Display helpful error and exit
- **No MP3 files found**: Display informative message and exit
- **Configuration errors**: Use defaults and warn user

### Error Recovery Strategy
- Individual file failures never stop the entire process
- All errors are logged with file paths and error details
- Final summary includes error count and details
- Exit codes indicate overall success/failure status

## Testing Strategy

### Unit Tests
- **File Scanner**: Test directory traversal, file filtering, validation
- **ID3 Processor**: Test tag detection, tag addition, error handling
- **Configuration**: Test loading, validation, defaults
- **Logger**: Test output formatting, error reporting

### Integration Tests
- **End-to-End Processing**: Test complete workflow with sample MP3 files
- **Error Scenarios**: Test handling of corrupted files, permission issues
- **Configuration Integration**: Test different configuration scenarios

### Test Data Requirements
- Sample MP3 files with various ID3 tag configurations:
  - Files with no genre/year tags
  - Files with existing genre but no year
  - Files with existing year but no genre
  - Files with both tags already present
  - Corrupted or invalid MP3 files

### Testing Tools
- **pytest**: Primary testing framework
- **pytest-mock**: For mocking file system operations
- **tempfile**: For creating temporary test directories
- **mutagen**: For creating test MP3 files with specific tag configurations

## Implementation Notes

### ID3 Tag Mapping
- **Genre**: Use ID3v2 TCON frame (Content Type)
- **Year**: Use ID3v2 TDRC frame (Recording Date) for ID3v2.4, TYER for older versions

### Mutagen Usage
- Use `mutagen.File()` for automatic format detection
- Access ID3 tags through the `.tags` attribute
- Use appropriate frame classes (ID3v2.3/2.4 compatibility)

### Performance Considerations
- Process files sequentially to avoid overwhelming the file system
- Use lazy loading for large directories
- Implement progress reporting for large collections

### Security Considerations
- Validate all file paths to prevent directory traversal
- Use safe file operations (atomic writes where possible)
- Handle symbolic links appropriately
- Respect file permissions and ownership