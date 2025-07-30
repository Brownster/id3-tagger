# MP3 ID3 Processor

A simple command-line tool that automatically adds missing genre and year ID3 tags to MP3 files in your music collection without modifying existing metadata.

## Features

- **Safe and Non-destructive**: Preserves all existing ID3 tags and metadata
- **Automatic Discovery**: Recursively scans your music directory for MP3 files
- **API Integration**: Uses the MusicBrainz API to lookup missing genre and year information
- **API Server Mode**: HTTP REST API for integration with other applications
- **Comprehensive Logging**: Detailed progress reporting and error handling
- **Dry Run Mode**: Preview changes before applying them
- **Flexible Configuration**: Command-line options and JSON configuration files

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Install from Source

1. Clone or download this repository
2. Navigate to the project directory
3. Install the package:

```bash
pip install .
```

### Install in Development Mode

For development or if you want to make changes:

```bash
pip install -e .
```

### Install Dependencies Only

If you want to run the application without installing:

```bash
pip install -r requirements.txt
```

## Quick Start

1. **Basic Usage**: Process all MP3 files in your ~/Music directory
   ```bash
   mp3-id3-processor
   ```

2. **Preview Changes**: See what would be modified without making changes
   ```bash
   mp3-id3-processor --dry-run
   ```

3. **Verbose Output**: Get detailed progress information
   ```bash
   mp3-id3-processor --verbose
   ```

## Usage Examples

### Basic Commands

```bash
# Process ~/Music with default settings
mp3-id3-processor

# Process a specific directory
mp3-id3-processor --directory /path/to/your/music

# Preview changes without modifying files
mp3-id3-processor --dry-run --verbose

# Disable API lookups (use only existing metadata)
mp3-id3-processor --no-api

# Use custom configuration file
mp3-id3-processor --config my-config.json
```

### Advanced Usage

```bash
# Custom API timeout and cache directory
mp3-id3-processor --api-timeout 15 --cache-dir ./api-cache

# Verbose dry run with custom directory
mp3-id3-processor --directory /media/music --dry-run --verbose

# Process with custom configuration and verbose output
mp3-id3-processor --config config.json --verbose
```

## API Server Mode

The application can run as an HTTP API server for integration with other applications that create MP3 files and want to automatically add missing ID3 metadata.

### Starting the API Server

```bash
# Start API server on default port (5000)
mp3-id3-processor --api-mode

# Start with verbose logging
mp3-id3-processor --api-mode --verbose
```

The server will start on `http://localhost:5000` by default.

### API Endpoints

#### Process Directory
**POST** `/process_directory`

Processes all MP3 files in a specified directory and adds missing genre and year tags.

**Request:**
```json
{
    "directory": "/path/to/mp3/files"
}
```

**Response:**
```json
{
    "processed": 15,
    "report": "api_report.txt"
}
```

#### Process Playlist
**POST** `/process_playlist`

Processes MP3 files listed in an M3U playlist file.

**Request:**
```json
{
    "m3u_path": "/path/to/playlist.m3u",
    "music_directory": "/optional/base/path"
}
```

**Response:**
```json
{
    "processed": 10,
    "report": "api_report.txt"
}
```

### API Usage Examples

```bash
# Process a directory via API
curl -X POST -H "Content-Type: application/json" \
     -d '{"directory": "/path/to/music"}' \
     http://localhost:5000/process_directory

# Process a playlist via API
curl -X POST -H "Content-Type: application/json" \
     -d '{"m3u_path": "/path/to/playlist.m3u"}' \
     http://localhost:5000/process_playlist
```

### Integration with Other Applications

The API server is designed for integration with applications that create MP3 files. For comprehensive integration documentation including code examples, error handling, and best practices, see [DEVELOPER_INTEGRATION.md](DEVELOPER_INTEGRATION.md).

**Basic Integration Example:**
```python
import requests

def add_missing_tags(output_directory):
    url = "http://localhost:5000/process_directory"
    payload = {"directory": output_directory}
    
    response = requests.post(url, 
                           headers={"Content-Type": "application/json"},
                           json=payload,
                           timeout=300)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Successfully processed {result['processed']} files")
        return True
    else:
        error = response.json()
        print(f"Error: {error['error']}")
        return False
```

## Command-Line Options

| Option | Description |
|--------|-------------|
| `--directory`, `-d` | Directory to scan for MP3 files (default: ~/Music) |
| `--no-api` | Disable API lookups and only process files with existing metadata |
| `--api-timeout` | API request timeout in seconds (default: 10.0) |
| `--cache-dir` | Directory for API response cache |
| `--config`, `-c` | Path to configuration file (JSON format) |
| `--verbose`, `-v` | Enable verbose output showing detailed progress |
| `--dry-run` | Show what would be done without making any changes |
| `--report-missing` | With `--dry-run`, report files missing genre or year |
| `--api-mode` | Start HTTP API server for integration with other applications |
| `--use-reissue-date` | Use actual reissue/remaster release dates instead of original release dates |
| `--help`, `-h` | Show help message and exit |

## Configuration

### Configuration File

Create a JSON configuration file to customize default behavior:

```json
{
  "music_directory": "~/Music",
  "use_api": true,
  "api_timeout": 10.0,
  "api_request_delay": 1.0,
  "api_cache_dir": null,
  "verbose": false,
  "original_release_date": true
}
```

### Configuration Options

- **music_directory**: Directory to scan for MP3 files
- **use_api**: Enable/disable MusicBrainz API lookups
- **api_timeout**: Timeout for API requests in seconds
- **api_request_delay**: Delay between API requests in seconds (MusicBrainz requires 1 req/sec)
- **api_cache_dir**: Directory for caching API responses
- **verbose**: Enable verbose logging
- **original_release_date**: Use original release dates from release-groups instead of reissue dates (default: true)

**Note**: The application only adds tags found via MusicBrainz API - no default values are used.

## How It Works

1. **Scanning**: Recursively scans the specified directory for MP3 files
2. **Analysis**: Examines each MP3 file to identify missing genre and year tags
3. **API Lookup**: Uses the MusicBrainz API to find missing genre and year information based on existing tags
4. **Safe Modification**: Adds only missing tags while preserving all existing metadata
5. **Reporting**: Provides detailed summary of all changes made

## API Integration

The application uses the MusicBrainz API to lookup missing genre and year information:

- Searches recordings by artist, album, and track title
- Returns the most popular genre tag found for the recording
- Retrieves the release year when available

## Safety Features

- **Non-destructive**: Never modifies existing ID3 tags
- **Error Handling**: Individual file errors don't stop the entire process
- **Backup Support**: Optional backup creation before modifications
- **Validation**: Validates file accessibility before processing
- **Dry Run**: Preview mode to see changes before applying

## Output Examples

### Normal Processing
```
Starting MP3 ID3 processing...
Found 150 MP3 files to process

[1/150] song1.mp3: Added genre (Rock) and year (1999)
[2/150] song2.mp3: Already had genre and year
[3/150] song3.mp3: Added genre (Pop)
[4/150] song4.mp3: Already has all tags
...

Processing Summary:
==================
Total files processed: 150
Files modified: 45
Tags added:
  genre: 25 files
Errors: 0
Processing completed successfully!
```

### Dry Run Mode
```
DRY RUN MODE - No files will be modified
--------------------------------------------------
Would add genre and year to: song1.mp3 (genre: Rock, year: 1999)
No changes for: song2.mp3 (already has genre and year)
Would add genre to: song3.mp3 (genre: Pop)
No changes for: song4.mp3 (already has all tags)
...

==================================================
DRY RUN SUMMARY
==================================================
Total files found: 150
Files that would be modified: 45
Tags that would be added:
  genre: 25 files
  year: 20 files
==================================================
```

## Troubleshooting

### Common Issues

**"No MP3 files found"**
- Check that the directory path is correct
- Ensure the directory contains MP3 files
- Verify directory permissions

**"Permission denied"**
- Check file and directory permissions
- Run with appropriate user privileges
- Ensure files are not locked by other applications

**"API lookup failed"**
- Check internet connection
- API may be temporarily unavailable
- Use `--no-api` flag to process without API lookups

**"Could not extract metadata"**
- File may be corrupted or not a valid MP3
- Check file integrity
- File will be skipped automatically

### Getting Help

Run with `--help` to see all available options:
```bash
mp3-id3-processor --help
```

Use `--verbose` flag for detailed processing information:
```bash
mp3-id3-processor --verbose
```

Use `--dry-run` to preview changes without modifying files:
```bash
mp3-id3-processor --dry-run --verbose
```

## Exit Codes

- **0**: Success - all files processed without errors
- **1**: Failure - all files failed to process
- **2**: Partial success - some files processed, some failed
- **130**: Interrupted by user (Ctrl+C)

## Requirements

See `requirements.txt` for the complete list of dependencies:
- mutagen: For MP3 file and ID3 tag manipulation
- requests: For API communication
- Additional standard library modules

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=mp3_id3_processor

# Run specific test file
python -m pytest tests/test_main.py
```

### Code Style

The project follows PEP 8 style guidelines. Use tools like `flake8` or `black` for code formatting.