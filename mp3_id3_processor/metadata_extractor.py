"""Metadata extractor for extracting existing ID3 tags from MP3 files."""

from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3NoHeaderError
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExistingMetadata:
    """Container for existing metadata extracted from MP3 files."""
    file_path: Path
    artist: Optional[str] = None
    album: Optional[str] = None
    title: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[str] = None
    has_genre: bool = False
    has_year: bool = False

    def __post_init__(self):
        """Validate and normalize metadata after initialization."""
        # Normalize strings - strip whitespace and convert empty strings to None
        self.artist = self._normalize_string(self.artist)
        self.album = self._normalize_string(self.album)
        self.title = self._normalize_string(self.title)
        self.genre = self._normalize_string(self.genre)
        self.year = self._normalize_string(self.year)
        
        # Update boolean flags based on actual content
        self.has_genre = self.genre is not None
        self.has_year = self.year is not None
    
    def _normalize_string(self, value: Optional[str]) -> Optional[str]:
        """Normalize string values by stripping whitespace and converting empty to None."""
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized if normalized else None
    
    def needs_genre(self) -> bool:
        """Check if this file needs a genre tag."""
        return not self.has_genre
    
    def needs_year(self) -> bool:
        """Check if this file needs a year tag."""
        return not self.has_year
    
    def needs_any_tags(self) -> bool:
        """Check if this file needs any tags."""
        return self.needs_genre() or self.needs_year()
    
    def has_lookup_info(self) -> bool:
        """Check if we have enough information to perform API lookups."""
        return self.artist is not None or self.title is not None
    
    def get_search_terms(self) -> Dict[str, str]:
        """Get search terms for API lookups."""
        terms = {}
        if self.artist:
            terms['artist'] = self.artist
        if self.album:
            terms['album'] = self.album
        if self.title:
            terms['title'] = self.title
        return terms


class MetadataExtractor:
    """Extracts existing metadata from MP3 files for API lookups."""
    
    def __init__(self):
        """Initialize the metadata extractor."""
        pass
    
    def extract_metadata(self, file_path: Path) -> Optional[ExistingMetadata]:
        """Extract existing metadata from an MP3 file.
        
        Args:
            file_path: Path to the MP3 file.
            
        Returns:
            ExistingMetadata object if successful, None if file cannot be processed.
        """
        try:
            # Load the MP3 file
            audio_file = self._load_mp3_file(file_path)
            if audio_file is None:
                logger.debug(f"Could not load MP3 file: {file_path}")
                return None
            
            # Extract metadata from ID3 tags
            metadata = ExistingMetadata(file_path=file_path)
            
            if audio_file.tags:
                metadata.artist = self._extract_artist(audio_file)
                metadata.album = self._extract_album(audio_file)
                metadata.title = self._extract_title(audio_file)
                metadata.genre = self._extract_genre(audio_file)
                metadata.year = self._extract_year(audio_file)
            
            logger.debug(f"Extracted metadata from {file_path.name}: "
                        f"artist='{metadata.artist}', album='{metadata.album}', "
                        f"title='{metadata.title}', genre='{metadata.genre}', year='{metadata.year}'")
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Error extracting metadata from {file_path}: {e}")
            return None
    
    def _load_mp3_file(self, file_path: Path) -> Optional[MP3]:
        """Load an MP3 file using Mutagen.
        
        Args:
            file_path: Path to the MP3 file.
            
        Returns:
            MP3 object if successful, None otherwise.
        """
        try:
            if not file_path.exists() or not file_path.is_file():
                return None
            
            # Try to load as MP3 file
            audio_file = MP3(str(file_path))
            
            # Validate that it's actually an MP3 file
            if audio_file.info is None:
                return None
            
            # Check if the file has valid audio info
            if not hasattr(audio_file.info, 'length') or audio_file.info.length <= 0:
                return None
            
            return audio_file
            
        except mutagen.mp3.HeaderNotFoundError:
            logger.debug(f"MP3 header not found: {file_path}")
            return None
        except mutagen.id3.ID3NoHeaderError:
            # MP3 file exists but has no ID3 header - still valid for our purposes
            try:
                audio_file = MP3(str(file_path))
                return audio_file
            except Exception:
                return None
        except mutagen.MutagenError as e:
            logger.debug(f"Mutagen error loading {file_path}: {e}")
            return None
        except Exception as e:
            logger.debug(f"Unexpected error loading {file_path}: {e}")
            return None
    
    def _extract_artist(self, audio_file: MP3) -> Optional[str]:
        """Extract artist information from ID3 tags."""
        try:
            # Try different artist tags in order of preference
            artist_tags = ['TPE1', 'TPE2', 'TOPE']  # Lead artist, Band, Original artist
            
            for tag in artist_tags:
                if tag in audio_file.tags:
                    frame = audio_file.tags[tag]
                    if frame.text and frame.text[0]:
                        artist = str(frame.text[0]).strip()
                        return artist if artist else None
            
            return None
            
        except (AttributeError, KeyError, IndexError):
            return None
    
    def _extract_album(self, audio_file: MP3) -> Optional[str]:
        """Extract album information from ID3 tags."""
        try:
            if 'TALB' in audio_file.tags:
                frame = audio_file.tags['TALB']
                if frame.text and frame.text[0]:
                    return str(frame.text[0]).strip()
            
            return None
            
        except (AttributeError, KeyError, IndexError):
            return None
    
    def _extract_title(self, audio_file: MP3) -> Optional[str]:
        """Extract title information from ID3 tags."""
        try:
            if 'TIT2' in audio_file.tags:
                frame = audio_file.tags['TIT2']
                if frame.text and frame.text[0]:
                    return str(frame.text[0]).strip()
            
            return None
            
        except (AttributeError, KeyError, IndexError):
            return None
    
    def _extract_genre(self, audio_file: MP3) -> Optional[str]:
        """Extract genre information from ID3 tags."""
        try:
            if 'TCON' in audio_file.tags:
                frame = audio_file.tags['TCON']
                if frame.text and frame.text[0]:
                    genre = str(frame.text[0]).strip()
                    # Filter out meaningless genres
                    if genre and genre.lower() not in ['unknown', 'other', '']:
                        return genre
            
            return None
            
        except (AttributeError, KeyError, IndexError):
            return None
    
    def _extract_year(self, audio_file: MP3) -> Optional[str]:
        """Extract year information from ID3 tags."""
        try:
            # Check for TDRC frame (Recording Date) - ID3v2.4
            if 'TDRC' in audio_file.tags:
                frame = audio_file.tags['TDRC']
                if frame.text and frame.text[0]:
                    year_str = str(frame.text[0]).strip()
                    if year_str and len(year_str) >= 4:
                        # Extract just the year part (first 4 digits)
                        year = year_str[:4]
                        if year.isdigit() and 1900 <= int(year) <= 2030:
                            return year
            
            # Check for TYER frame (Year) - ID3v2.3 and earlier
            if 'TYER' in audio_file.tags:
                frame = audio_file.tags['TYER']
                if frame.text and frame.text[0]:
                    year_str = str(frame.text[0]).strip()
                    if year_str and year_str.isdigit() and 1900 <= int(year_str) <= 2030:
                        return year_str
            
            return None
            
        except (AttributeError, KeyError, IndexError, ValueError):
            return None
    
    def extract_batch_metadata(self, file_paths: list[Path]) -> Dict[Path, ExistingMetadata]:
        """Extract metadata from multiple files.
        
        Args:
            file_paths: List of MP3 file paths.
            
        Returns:
            Dictionary mapping file paths to their metadata.
        """
        results = {}
        
        for file_path in file_paths:
            metadata = self.extract_metadata(file_path)
            if metadata:
                results[file_path] = metadata
            else:
                logger.warning(f"Could not extract metadata from: {file_path}")
        
        return results
    
    def get_files_needing_tags(self, metadata_dict: Dict[Path, ExistingMetadata]) -> Dict[Path, ExistingMetadata]:
        """Filter files that need genre or year tags.
        
        Args:
            metadata_dict: Dictionary of file paths to metadata.
            
        Returns:
            Dictionary containing only files that need tags.
        """
        return {
            path: metadata 
            for path, metadata in metadata_dict.items() 
            if metadata.needs_any_tags()
        }
    
    def get_files_with_lookup_info(self, metadata_dict: Dict[Path, ExistingMetadata]) -> Dict[Path, ExistingMetadata]:
        """Filter files that have enough information for API lookups.
        
        Args:
            metadata_dict: Dictionary of file paths to metadata.
            
        Returns:
            Dictionary containing only files with lookup information.
        """
        return {
            path: metadata 
            for path, metadata in metadata_dict.items() 
            if metadata.has_lookup_info()
        }