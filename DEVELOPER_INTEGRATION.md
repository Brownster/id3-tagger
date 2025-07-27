# MP3 ID3 Tagger - Developer Integration Guide

## Overview

The MP3 ID3 Tagger provides a REST API that allows developers to integrate automatic genre and year tagging into their applications. This is particularly useful for applications that create MP3 files and want to automatically add missing ID3 metadata.

## Quick Start

### Starting the API Server

```bash
# Install the package
pip install mp3-id3-processor

# Start the API server (default: http://localhost:5000)
mp3-id3-processor --api-mode

# Or with custom host/port
mp3-id3-processor --api-mode --host 0.0.0.0 --port 8080
```

### Basic Integration Example

```python
import requests
import json

# After your app creates MP3 files, call the API to add missing tags
def add_missing_tags(output_directory):
    url = "http://localhost:5000/process_directory"
    payload = {"directory": output_directory}
    
    response = requests.post(url, 
                           headers={"Content-Type": "application/json"},
                           json=payload,
                           timeout=300)  # 5 minute timeout
    
    if response.status_code == 200:
        result = response.json()
        print(f"Successfully processed {result['processed']} files")
        print(f"Report saved to: {result['report']}")
        return True
    else:
        error = response.json()
        print(f"Error: {error['error']}")
        return False

# Example usage in your MP3 creation workflow
def your_mp3_creation_function():
    output_dir = "/path/to/your/mp3/output"
    
    # Your existing code that creates MP3 files
    create_mp3_files(output_dir)
    
    # Add missing genre and year tags
    add_missing_tags(output_dir)
```

## API Endpoints

### 1. Process Directory

**Endpoint:** `POST /process_directory`

Processes all MP3 files in a specified directory and adds missing genre and year tags.

**Request:**
```json
{
    "directory": "/path/to/mp3/files"
}
```

**Response (Success):**
```json
{
    "processed": 15,
    "report": "api_report.txt"
}
```

**Response (Error):**
```json
{
    "error": "Directory does not exist: /invalid/path"
}
```

### 2. Process Playlist

**Endpoint:** `POST /process_playlist`

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

## Integration Patterns

### Pattern 1: Post-Processing Hook

Add the API call as a post-processing step after your MP3 creation:

```python
class MP3Creator:
    def __init__(self):
        self.tagger_api_url = "http://localhost:5000"
    
    def create_album(self, tracks, output_dir):
        # Create MP3 files
        for track in tracks:
            self.create_mp3_file(track, output_dir)
        
        # Add missing ID3 tags
        self.add_missing_tags(output_dir)
    
    def add_missing_tags(self, directory):
        try:
            response = requests.post(
                f"{self.tagger_api_url}/process_directory",
                json={"directory": str(directory)},
                timeout=300
            )
            if response.status_code == 200:
                result = response.json()
                self.log(f"Tagged {result['processed']} files")
            else:
                self.log(f"Tagging failed: {response.json()['error']}")
        except requests.exceptions.RequestException as e:
            self.log(f"Tagging service unavailable: {e}")
```

### Pattern 2: Batch Processing

For applications that create many files, batch them for efficient processing:

```python
class BatchMP3Processor:
    def __init__(self):
        self.pending_directories = []
        self.tagger_api_url = "http://localhost:5000"
    
    def add_completed_directory(self, directory):
        """Add a directory to be processed for missing tags"""
        self.pending_directories.append(directory)
    
    def process_pending_tags(self):
        """Process all pending directories for missing tags"""
        for directory in self.pending_directories:
            self.tag_directory(directory)
        self.pending_directories.clear()
    
    def tag_directory(self, directory):
        response = requests.post(
            f"{self.tagger_api_url}/process_directory",
            json={"directory": str(directory)},
            timeout=300
        )
        return response.status_code == 200
```

### Pattern 3: Playlist Integration

For applications that work with playlists:

```python
def process_playlist_tags(playlist_path, music_base_path=None):
    """Add missing tags to all files in a playlist"""
    payload = {"m3u_path": playlist_path}
    if music_base_path:
        payload["music_directory"] = music_base_path
    
    response = requests.post(
        "http://localhost:5000/process_playlist",
        json=payload,
        timeout=600  # Longer timeout for playlists
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Playlist processing failed: {response.json()['error']}")
```

## Configuration

### Default Configuration

The API server uses these settings:
- **API Lookups:** Enabled (uses MusicBrainz)
- **Rate Limiting:** 1 request/second (MusicBrainz compliance)
- **Tag Sources:** Only adds genres and years found via MusicBrainz API (no defaults)

### Custom Configuration

You can customize the server behavior by creating a configuration file:

```json
{
    "use_api": true,
    "api_timeout": 10.0,
    "api_request_delay": 1.0,
    "verbose": false
}
```

Start the server with custom config:
```bash
mp3-id3-processor --api-mode --config custom_config.json
```

## Response Processing

### Processing Reports

Each API call generates a detailed report file with processing statistics:

```
PROCESSING SUMMARY
==================
Total files found: 25
Files processed: 25
Files modified: 18
Tags added:
  genre: 15 files
  year: 18 files
Errors:
  track_with_issue.mp3: Could not extract metadata
```

### Handling the Report

```python
def process_report(report_path):
    """Parse and handle the processing report"""
    try:
        with open(report_path, 'r') as f:
            report_content = f.read()
        
        # Extract statistics from report
        lines = report_content.split('\n')
        stats = {}
        for line in lines:
            if 'Total files found:' in line:
                stats['total'] = int(line.split(':')[1].strip())
            elif 'Files modified:' in line:
                stats['modified'] = int(line.split(':')[1].strip())
        
        return stats
    except FileNotFoundError:
        return None
```

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `"directory required"` | Missing directory parameter | Ensure JSON payload includes "directory" field |
| `"Directory does not exist"` | Invalid path | Verify the directory path exists and is accessible |
| `"m3u_path required"` | Missing playlist parameter | Ensure JSON payload includes "m3u_path" field |
| Connection timeout | API server not running | Start the API server with `--api-mode` |
| Rate limiting delays | Many files to process | This is normal - MusicBrainz requires 1 req/sec |

### Robust Error Handling

```python
def robust_tag_processing(directory, max_retries=3):
    """Process directory with retry logic"""
    url = "http://localhost:5000/process_directory"
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                url,
                json={"directory": directory},
                timeout=300
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                # Client error - don't retry
                error = response.json()
                raise ValueError(f"Invalid request: {error['error']}")
            else:
                # Server error - might retry
                if attempt == max_retries - 1:
                    raise Exception(f"Server error after {max_retries} attempts")
                time.sleep(2 ** attempt)  # Exponential backoff
                
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise Exception(f"Connection failed: {e}")
            time.sleep(2 ** attempt)
    
    return None
```

## Performance Considerations

### Processing Time Estimates

The API respects MusicBrainz rate limits (1 request/second), so processing time depends on the number of files needing tags:

- **10 files needing tags:** ~10-15 seconds
- **50 files needing tags:** ~50-60 seconds  
- **100 files needing tags:** ~100-120 seconds

### Optimization Tips

1. **Pre-check files:** Only call the API for directories containing files that actually need tags
2. **Batch processing:** Process multiple directories in sequence rather than parallel
3. **Async integration:** Don't block your main UI/workflow while tagging runs
4. **Timeout handling:** Set appropriate timeouts based on expected file counts

```python
import os
from pathlib import Path

def estimate_processing_time(directory):
    """Estimate how long tagging will take"""
    mp3_files = list(Path(directory).glob("**/*.mp3"))
    
    # Rough estimate: 1.2 seconds per file (includes API + processing overhead)
    estimated_seconds = len(mp3_files) * 1.2
    
    return {
        'file_count': len(mp3_files),
        'estimated_seconds': estimated_seconds,
        'estimated_minutes': estimated_seconds / 60
    }

def should_process_directory(directory):
    """Check if directory likely needs processing"""
    estimate = estimate_processing_time(directory)
    
    # Skip if no MP3 files or too many (might want to process separately)
    if estimate['file_count'] == 0:
        return False
    if estimate['file_count'] > 200:  # Might take 4+ minutes
        return False
        
    return True
```

## Deployment Considerations

### Production Deployment

For production use, consider:

1. **Process Management:** Use a process manager like systemd or supervisor
2. **Reverse Proxy:** Put nginx or Apache in front for better performance
3. **Monitoring:** Monitor the API server health and response times
4. **Scaling:** For high volume, consider multiple server instances

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install mp3-id3-processor

EXPOSE 5000

CMD ["mp3-id3-processor", "--api-mode", "--host", "0.0.0.0", "--port", "5000"]
```

### Health Check Endpoint

You can check if the API server is running:

```bash
curl -f http://localhost:5000/process_directory || echo "API server not responding"
```

## Security Considerations

### Path Validation

Always validate directory paths to prevent directory traversal attacks:

```python
import os
from pathlib import Path

def validate_directory_path(directory_path, allowed_base_paths):
    """Validate that directory path is within allowed locations"""
    try:
        resolved_path = Path(directory_path).resolve()
        
        for base_path in allowed_base_paths:
            if resolved_path.is_relative_to(Path(base_path).resolve()):
                return str(resolved_path)
        
        raise ValueError(f"Directory not in allowed paths: {directory_path}")
    except Exception:
        raise ValueError(f"Invalid directory path: {directory_path}")

# Usage
allowed_paths = ["/home/user/music", "/tmp/mp3_output"]
safe_path = validate_directory_path(user_input, allowed_paths)
```

### Network Security

- Run the API server on localhost (127.0.0.1) unless remote access is needed
- Use HTTPS in production with proper certificates
- Implement authentication if exposed to multiple users
- Consider firewall rules to restrict access

## Testing Your Integration

### Unit Test Example

```python
import unittest
from unittest.mock import patch, Mock
import requests

class TestMP3TaggerIntegration(unittest.TestCase):
    
    def setUp(self):
        self.api_url = "http://localhost:5000"
        self.test_directory = "/tmp/test_mp3s"
    
    @patch('requests.post')
    def test_successful_processing(self, mock_post):
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "processed": 5,
            "report": "api_report.txt"
        }
        mock_post.return_value = mock_response
        
        # Test your integration function
        result = add_missing_tags(self.test_directory)
        
        self.assertTrue(result)
        mock_post.assert_called_once_with(
            f"{self.api_url}/process_directory",
            headers={"Content-Type": "application/json"},
            json={"directory": self.test_directory},
            timeout=300
        )
    
    @patch('requests.post')
    def test_api_error_handling(self, mock_post):
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": "Directory does not exist"
        }
        mock_post.return_value = mock_response
        
        result = add_missing_tags("/invalid/path")
        
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
```

## Support and Troubleshooting

### Common Integration Issues

1. **API server not starting:** Check if port 5000 is available
2. **Slow responses:** Normal due to MusicBrainz rate limiting (1 req/sec)
3. **No tags added:** Files may already have complete metadata
4. **Connection refused:** Ensure API server is running and accessible

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
mp3-id3-processor --api-mode --verbose
```

### Getting Help

- Check the main README.md for general usage
- Review the API server logs for detailed error messages
- Ensure your MP3 files have sufficient metadata (artist, album, title) for API lookups

## Example: Complete Integration

Here's a complete example showing how to integrate the tagger into an MP3 creation application:

```python
import requests
import json
import logging
from pathlib import Path
import time

class MP3TaggerIntegration:
    def __init__(self, api_base_url="http://localhost:5000"):
        self.api_base_url = api_base_url
        self.logger = logging.getLogger(__name__)
    
    def is_api_available(self):
        """Check if the MP3 tagger API is available"""
        try:
            # Try a simple request to see if server responds
            response = requests.post(
                f"{self.api_base_url}/process_directory",
                json={"directory": "/nonexistent"},
                timeout=5
            )
            # Even a 400 error means the server is responding
            return True
        except requests.exceptions.RequestException:
            return False
    
    def add_missing_tags(self, directory, timeout=300):
        """Add missing genre and year tags to all MP3s in directory"""
        if not self.is_api_available():
            self.logger.warning("MP3 tagger API not available, skipping tag addition")
            return False
        
        try:
            self.logger.info(f"Adding missing tags to MP3s in: {directory}")
            
            response = requests.post(
                f"{self.api_base_url}/process_directory",
                json={"directory": str(directory)},
                headers={"Content-Type": "application/json"},
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"Successfully processed {result['processed']} files")
                
                # Optionally read and log the detailed report
                if 'report' in result:
                    self.log_processing_report(result['report'])
                
                return True
            else:
                error = response.json()
                self.logger.error(f"Failed to add tags: {error['error']}")
                return False
                
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout adding tags to {directory}")
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error adding tags: {e}")
            return False
    
    def log_processing_report(self, report_path):
        """Read and log the processing report"""
        try:
            with open(report_path, 'r') as f:
                report = f.read()
            self.logger.info(f"Processing report:\n{report}")
        except FileNotFoundError:
            self.logger.warning(f"Report file not found: {report_path}")
    
    def add_tags_to_playlist(self, playlist_path, music_directory=None, timeout=600):
        """Add missing tags to files in a playlist"""
        if not self.is_api_available():
            self.logger.warning("MP3 tagger API not available, skipping tag addition")
            return False
        
        payload = {"m3u_path": str(playlist_path)}
        if music_directory:
            payload["music_directory"] = str(music_directory)
        
        try:
            response = requests.post(
                f"{self.api_base_url}/process_playlist",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"Successfully processed {result['processed']} playlist files")
                return True
            else:
                error = response.json()
                self.logger.error(f"Failed to add playlist tags: {error['error']}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error adding playlist tags: {e}")
            return False

# Usage example in your MP3 creation application
class YourMP3CreationApp:
    def __init__(self):
        self.tagger = MP3TaggerIntegration()
        self.logger = logging.getLogger(__name__)
    
    def create_album(self, tracks, output_directory):
        """Create an album of MP3 files and add missing metadata"""
        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Your existing MP3 creation logic
        self.logger.info(f"Creating {len(tracks)} MP3 files in {output_dir}")
        for track in tracks:
            self.create_single_mp3(track, output_dir)
        
        # Add missing genre and year tags
        self.logger.info("Adding missing ID3 tags...")
        success = self.tagger.add_missing_tags(output_dir)
        
        if success:
            self.logger.info("Album creation and tagging completed successfully")
        else:
            self.logger.warning("Album created but tagging failed")
        
        return success
    
    def create_single_mp3(self, track_info, output_dir):
        """Your existing MP3 creation logic"""
        # Implementation depends on your application
        pass

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    app = YourMP3CreationApp()
    
    # Example track list
    tracks = [
        {"title": "Song 1", "artist": "Artist A", "album": "Test Album"},
        {"title": "Song 2", "artist": "Artist A", "album": "Test Album"},
    ]
    
    app.create_album(tracks, "/tmp/my_album_output")
```

This integration guide provides everything a developer needs to successfully integrate the MP3 ID3 Tagger API into their application for automatic metadata enhancement.