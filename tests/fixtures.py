"""Test fixtures and utilities for MP3 ID3 processor tests.

This module provides utilities to create sample MP3 files with various
ID3 tag configurations for comprehensive testing.
"""

import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Any
import pytest
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TDRC, TYER, TRCK


class MP3TestFileGenerator:
    """Utility class for generating test MP3 files with specific ID3 tag configurations."""
    
    def __init__(self, temp_dir: Path):
        """Initialize the generator with a temporary directory.
        
        Args:
            temp_dir: Directory where test files will be created
        """
        self.temp_dir = temp_dir
        self.created_files: List[Path] = []
    
    def create_minimal_mp3_file(self, filename: str) -> Path:
        """Create a minimal valid MP3 file.
        
        Args:
            filename: Name of the file to create
            
        Returns:
            Path to the created file
        """
        file_path = self.temp_dir / filename
        
        # Create a more complete MP3 file structure that Mutagen can parse
        # Start with ID3v2 header (empty for now)
        id3v2_header = bytes([
            0x49, 0x44, 0x33,  # "ID3"
            0x03, 0x00,        # Version 2.3.0
            0x00,              # Flags
            0x00, 0x00, 0x00, 0x00  # Size (0 for now)
        ])
        
        # Create a valid MP3 frame header
        # MPEG-1 Layer 3, 128kbps, 44.1kHz, no padding, no CRC
        mp3_frame_header = bytes([
            0xFF, 0xFB,  # Sync word (11 bits) + MPEG version + Layer
            0x90,        # Bitrate index (128kbps) + Sample rate (44.1kHz)
            0x00         # Padding + Private + Mode + Mode extension + Copyright + Original + Emphasis
        ])
        
        # Calculate frame size for 128kbps at 44.1kHz
        # Frame size = (144 * bitrate) / sample_rate + padding
        # For 128kbps at 44.1kHz: (144 * 128000) / 44100 = ~417 bytes
        frame_size = 417
        
        # Create frame data (mostly silence with some variation to avoid sync issues)
        frame_data = bytearray(frame_size - 4)  # -4 for header
        # Add some non-zero bytes to make it more realistic
        for i in range(0, len(frame_data), 50):
            frame_data[i] = 0x55  # Alternating pattern
        
        # Create multiple frames to ensure Mutagen can sync
        frames_data = b''
        for _ in range(5):  # Create 5 frames
            frames_data += mp3_frame_header + bytes(frame_data)
        
        with open(file_path, 'wb') as f:
            f.write(id3v2_header + frames_data)
        
        self.created_files.append(file_path)
        return file_path
    
    def add_id3_tags(self, file_path: Path, tags: Dict[str, Any]) -> None:
        """Add ID3 tags to an MP3 file.
        
        Args:
            file_path: Path to the MP3 file
            tags: Dictionary of tag names to values
        """
        try:
            audio = MP3(file_path)
            if audio.tags is None:
                audio.add_tags()
            
            # Map common tag names to ID3 frames
            tag_mapping = {
                'title': TIT2,
                'artist': TPE1,
                'album': TALB,
                'genre': TCON,
                'year': TDRC,  # Use TDRC for ID3v2.4
                'year_legacy': TYER,  # Use TYER for ID3v2.3
                'track': TRCK,
            }
            
            for tag_name, value in tags.items():
                if tag_name in tag_mapping:
                    frame_class = tag_mapping[tag_name]
                    audio.tags.add(frame_class(encoding=3, text=str(value)))
            
            audio.save()
        except Exception as e:
            raise RuntimeError(f"Failed to add tags to {file_path}: {e}")
    
    def create_mp3_with_tags(self, filename: str, tags: Dict[str, Any]) -> Path:
        """Create an MP3 file with specific ID3 tags.
        
        Args:
            filename: Name of the file to create
            tags: Dictionary of tag names to values
            
        Returns:
            Path to the created file
        """
        file_path = self.create_minimal_mp3_file(filename)
        self.add_id3_tags(file_path, tags)
        return file_path
    
    def create_corrupted_mp3(self, filename: str) -> Path:
        """Create a corrupted MP3 file that will cause parsing errors.
        
        Args:
            filename: Name of the file to create
            
        Returns:
            Path to the created file
        """
        file_path = self.temp_dir / filename
        
        # Create a file with MP3 extension but invalid content
        with open(file_path, 'wb') as f:
            f.write(b'This is not a valid MP3 file content')
        
        self.created_files.append(file_path)
        return file_path
    
    def create_empty_mp3(self, filename: str) -> Path:
        """Create an empty file with MP3 extension.
        
        Args:
            filename: Name of the file to create
            
        Returns:
            Path to the created file
        """
        file_path = self.temp_dir / filename
        file_path.touch()
        self.created_files.append(file_path)
        return file_path
    
    def cleanup(self):
        """Clean up all created test files."""
        for file_path in self.created_files:
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception:
                    pass  # Ignore cleanup errors
        self.created_files.clear()


class TestDataSets:
    """Predefined test data sets for various testing scenarios."""
    
    @staticmethod
    def get_missing_genre_files() -> List[Dict[str, Any]]:
        """Get file configurations for testing missing genre tags.
        
        Returns:
            List of file configurations with missing genre tags
        """
        return [
            {
                'filename': 'missing_genre_1.mp3',
                'tags': {
                    'title': 'Song Without Genre',
                    'artist': 'Test Artist',
                    'album': 'Test Album',
                    'year': '2023',
                    'track': '1'
                }
            },
            {
                'filename': 'missing_genre_2.mp3',
                'tags': {
                    'title': 'Another Song',
                    'artist': 'Another Artist',
                    'year': '2022'
                }
            },
            {
                'filename': 'missing_genre_minimal.mp3',
                'tags': {
                    'title': 'Minimal Song'
                }
            }
        ]
    
    @staticmethod
    def get_missing_year_files() -> List[Dict[str, Any]]:
        """Get file configurations for testing missing year tags.
        
        Returns:
            List of file configurations with missing year tags
        """
        return [
            {
                'filename': 'missing_year_1.mp3',
                'tags': {
                    'title': 'Song Without Year',
                    'artist': 'Test Artist',
                    'album': 'Test Album',
                    'genre': 'Rock',
                    'track': '1'
                }
            },
            {
                'filename': 'missing_year_2.mp3',
                'tags': {
                    'title': 'Another Song',
                    'artist': 'Another Artist',
                    'genre': 'Pop'
                }
            },
            {
                'filename': 'missing_year_minimal.mp3',
                'tags': {
                    'genre': 'Jazz'
                }
            }
        ]
    
    @staticmethod
    def get_missing_both_files() -> List[Dict[str, Any]]:
        """Get file configurations for testing missing both genre and year tags.
        
        Returns:
            List of file configurations with missing both tags
        """
        return [
            {
                'filename': 'missing_both_1.mp3',
                'tags': {
                    'title': 'Song Without Genre and Year',
                    'artist': 'Test Artist',
                    'album': 'Test Album',
                    'track': '1'
                }
            },
            {
                'filename': 'missing_both_2.mp3',
                'tags': {
                    'title': 'Another Song',
                    'artist': 'Another Artist'
                }
            },
            {
                'filename': 'missing_both_minimal.mp3',
                'tags': {
                    'title': 'Minimal Song'
                }
            },
            {
                'filename': 'missing_both_empty_tags.mp3',
                'tags': {}  # No tags at all
            }
        ]
    
    @staticmethod
    def get_complete_files() -> List[Dict[str, Any]]:
        """Get file configurations for testing files with complete tags.
        
        Returns:
            List of file configurations with all required tags
        """
        return [
            {
                'filename': 'complete_1.mp3',
                'tags': {
                    'title': 'Complete Song',
                    'artist': 'Test Artist',
                    'album': 'Test Album',
                    'genre': 'Rock',
                    'year': '2023',
                    'track': '1'
                }
            },
            {
                'filename': 'complete_2.mp3',
                'tags': {
                    'title': 'Another Complete Song',
                    'artist': 'Another Artist',
                    'album': 'Another Album',
                    'genre': 'Pop',
                    'year': '2022',
                    'track': '2'
                }
            }
        ]
    
    @staticmethod
    def get_mixed_scenario_files() -> List[Dict[str, Any]]:
        """Get file configurations for mixed testing scenarios.
        
        Returns:
            List of file configurations with various tag combinations
        """
        files = []
        files.extend(TestDataSets.get_missing_genre_files()[:1])
        files.extend(TestDataSets.get_missing_year_files()[:1])
        files.extend(TestDataSets.get_missing_both_files()[:2])
        files.extend(TestDataSets.get_complete_files()[:1])
        return files
    
    @staticmethod
    def get_error_test_files() -> List[Dict[str, Any]]:
        """Get file configurations for error testing scenarios.
        
        Returns:
            List of file configurations for error testing
        """
        return [
            {
                'filename': 'corrupted.mp3',
                'type': 'corrupted'
            },
            {
                'filename': 'empty.mp3',
                'type': 'empty'
            },
            {
                'filename': 'not_mp3.txt',
                'type': 'wrong_extension',
                'tags': {'title': 'Not an MP3'}
            }
        ]


@pytest.fixture
def temp_music_dir():
    """Create a temporary directory for test music files.
    
    Yields:
        Path to temporary directory
    """
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


@pytest.fixture
def mp3_generator(temp_music_dir):
    """Create an MP3TestFileGenerator instance.
    
    Args:
        temp_music_dir: Temporary directory fixture
        
    Yields:
        MP3TestFileGenerator instance
    """
    generator = MP3TestFileGenerator(temp_music_dir)
    try:
        yield generator
    finally:
        generator.cleanup()


@pytest.fixture
def sample_mp3_files(mp3_generator):
    """Create a set of sample MP3 files for testing.
    
    Args:
        mp3_generator: MP3TestFileGenerator fixture
        
    Returns:
        Dictionary mapping scenario names to lists of created file paths
    """
    files = {}
    
    # Create files with missing genre tags
    files['missing_genre'] = []
    for file_config in TestDataSets.get_missing_genre_files():
        file_path = mp3_generator.create_mp3_with_tags(
            file_config['filename'], 
            file_config['tags']
        )
        files['missing_genre'].append(file_path)
    
    # Create files with missing year tags
    files['missing_year'] = []
    for file_config in TestDataSets.get_missing_year_files():
        file_path = mp3_generator.create_mp3_with_tags(
            file_config['filename'], 
            file_config['tags']
        )
        files['missing_year'].append(file_path)
    
    # Create files with missing both tags
    files['missing_both'] = []
    for file_config in TestDataSets.get_missing_both_files():
        file_path = mp3_generator.create_mp3_with_tags(
            file_config['filename'], 
            file_config['tags']
        )
        files['missing_both'].append(file_path)
    
    # Create files with complete tags
    files['complete'] = []
    for file_config in TestDataSets.get_complete_files():
        file_path = mp3_generator.create_mp3_with_tags(
            file_config['filename'], 
            file_config['tags']
        )
        files['complete'].append(file_path)
    
    # Create error test files
    files['error_files'] = []
    for file_config in TestDataSets.get_error_test_files():
        if file_config.get('type') == 'corrupted':
            file_path = mp3_generator.create_corrupted_mp3(file_config['filename'])
        elif file_config.get('type') == 'empty':
            file_path = mp3_generator.create_empty_mp3(file_config['filename'])
        else:
            # Create regular file with wrong extension
            file_path = mp3_generator.create_mp3_with_tags(
                file_config['filename'], 
                file_config.get('tags', {})
            )
        files['error_files'].append(file_path)
    
    return files


@pytest.fixture
def mixed_scenario_files(mp3_generator):
    """Create a mixed set of MP3 files for comprehensive testing.
    
    Args:
        mp3_generator: MP3TestFileGenerator fixture
        
    Returns:
        List of created file paths with various tag configurations
    """
    files = []
    for file_config in TestDataSets.get_mixed_scenario_files():
        file_path = mp3_generator.create_mp3_with_tags(
            file_config['filename'], 
            file_config['tags']
        )
        files.append(file_path)
    
    return files


def verify_mp3_tags(file_path: Path, expected_tags: Dict[str, str]) -> bool:
    """Verify that an MP3 file has the expected tags.
    
    Args:
        file_path: Path to the MP3 file
        expected_tags: Dictionary of expected tag names to values
        
    Returns:
        True if all expected tags are present and correct
    """
    try:
        audio = MP3(file_path)
        if audio.tags is None:
            return len(expected_tags) == 0
        
        # Check each expected tag
        for tag_name, expected_value in expected_tags.items():
            if tag_name == 'genre':
                actual_value = audio.tags.get('TCON')
                if actual_value is None:
                    return False
                if str(actual_value[0]) != expected_value:
                    return False
            elif tag_name == 'year':
                # Check both TDRC (ID3v2.4) and TYER (ID3v2.3)
                actual_value = audio.tags.get('TDRC') or audio.tags.get('TYER')
                if actual_value is None:
                    return False
                if str(actual_value[0]) != expected_value:
                    return False
            elif tag_name == 'title':
                actual_value = audio.tags.get('TIT2')
                if actual_value is None:
                    return False
                if str(actual_value[0]) != expected_value:
                    return False
            elif tag_name == 'artist':
                actual_value = audio.tags.get('TPE1')
                if actual_value is None:
                    return False
                if str(actual_value[0]) != expected_value:
                    return False
            elif tag_name == 'album':
                actual_value = audio.tags.get('TALB')
                if actual_value is None:
                    return False
                if str(actual_value[0]) != expected_value:
                    return False
        
        return True
    except Exception:
        return False


def get_mp3_tag_value(file_path: Path, tag_name: str) -> Optional[str]:
    """Get the value of a specific tag from an MP3 file.
    
    Args:
        file_path: Path to the MP3 file
        tag_name: Name of the tag to retrieve
        
    Returns:
        Tag value as string, or None if not found
    """
    try:
        audio = MP3(file_path)
        if audio.tags is None:
            return None
        
        if tag_name == 'genre':
            tag = audio.tags.get('TCON')
        elif tag_name == 'year':
            tag = audio.tags.get('TDRC') or audio.tags.get('TYER')
        elif tag_name == 'title':
            tag = audio.tags.get('TIT2')
        elif tag_name == 'artist':
            tag = audio.tags.get('TPE1')
        elif tag_name == 'album':
            tag = audio.tags.get('TALB')
        else:
            return None
        
        return str(tag[0]) if tag else None
    except Exception:
        return None