"""ID3 processor module for handling tag manipulation."""

from pathlib import Path
from typing import List, Optional, Union
import mutagen
from mutagen.id3 import ID3, TCON, TDRC, TYER, ID3NoHeaderError
from mutagen.mp3 import MP3
from .models import ProcessingResult
from .config import Configuration


class ID3Processor:
    """Handles ID3 tag processing for MP3 files using Mutagen."""
    
    def __init__(self, config: Configuration, dry_run: bool = False):
        """Initialize the ID3 processor with configuration.
        
        Args:
            config: Configuration instance containing default values.
            dry_run: If True, don't actually modify files.
        """
        self.config = config
        self.dry_run = dry_run
    
    def process_file(self, file_path: Path) -> ProcessingResult:
        """Process a single MP3 file to add missing tags.
        
        Args:
            file_path: Path to the MP3 file to process.
            
        Returns:
            ProcessingResult with details of the processing outcome.
        """
        try:
            # Load the MP3 file
            audio_file = self._load_mp3_file(file_path)
            if audio_file is None:
                return ProcessingResult(
                    file_path=file_path,
                    success=False,
                    error_message="Failed to load MP3 file"
                )
            
            # Check what tags need to be added
            tags_to_add = []
            
            if self.needs_genre_tag(audio_file):
                tags_to_add.append('genre')
            
            if self.needs_year_tag(audio_file):
                tags_to_add.append('year')
            
            # If no tags need to be added, return success with empty tags_added
            if not tags_to_add:
                return ProcessingResult(
                    file_path=file_path,
                    success=True,
                    tags_added=[]
                )
            
            # Add missing tags using configuration defaults
            added_tags = self.add_missing_tags(audio_file, file_path)
            
            return ProcessingResult(
                file_path=file_path,
                success=True,
                tags_added=added_tags
            )
            
        except Exception as e:
            return ProcessingResult(
                file_path=file_path,
                success=False,
                error_message=str(e)
            )
    
    def _load_mp3_file(self, file_path: Path) -> Optional[MP3]:
        """Load an MP3 file using Mutagen with comprehensive error handling.
        
        Args:
            file_path: Path to the MP3 file.
            
        Returns:
            MP3 object if successful, None otherwise.
        """
        try:
            # Check if file exists and is readable
            if not file_path.exists():
                return None
            
            if not file_path.is_file():
                return None
            
            # Try to load as MP3 file
            audio_file = MP3(str(file_path))
            
            # Validate that it's actually an MP3 file
            if audio_file.info is None:
                return None
            
            # Check if the file has valid audio info
            if not hasattr(audio_file.info, 'length') or audio_file.info.length <= 0:
                return None
            
            # Ensure ID3 tags exist (create if they don't)
            if audio_file.tags is None:
                try:
                    audio_file.add_tags()
                except Exception:
                    # If we can't add tags, the file might be read-only or corrupted
                    return None
            
            return audio_file
            
        except mutagen.mp3.HeaderNotFoundError:
            # Not a valid MP3 file or corrupted header
            return None
        except mutagen.id3.ID3NoHeaderError:
            # MP3 file exists but has no ID3 header - this is recoverable
            try:
                audio_file = MP3(str(file_path))
                audio_file.add_tags()
                return audio_file
            except Exception:
                return None
        except mutagen.MutagenError:
            # General Mutagen errors - unsupported format or corrupted file
            return None
        except (OSError, IOError, PermissionError):
            # File system errors - permission denied, file locked, etc.
            return None
        except (ValueError, TypeError):
            # Invalid file path or other value errors
            return None
        except Exception:
            # Catch any other unexpected errors
            return None
    
    def needs_genre_tag(self, audio_file: MP3) -> bool:
        """Check if the MP3 file needs a genre tag.
        
        Args:
            audio_file: MP3 object to check.
            
        Returns:
            True if genre tag is missing or empty, False otherwise.
        """
        try:
            # Check for TCON frame (Content Type/Genre)
            if 'TCON' not in audio_file.tags:
                return True
            
            # Check if the genre value is empty or just whitespace
            genre_frame = audio_file.tags['TCON']
            if not genre_frame.text or not any(str(text).strip() for text in genre_frame.text):
                return True
            
            return False
            
        except (AttributeError, KeyError):
            return True
    
    def needs_year_tag(self, audio_file: MP3) -> bool:
        """Check if the MP3 file needs a year tag.
        
        Args:
            audio_file: MP3 object to check.
            
        Returns:
            True if year tag is missing or empty, False otherwise.
        """
        try:
            # Check for TDRC frame (Recording Date) - ID3v2.4
            if 'TDRC' in audio_file.tags:
                tdrc_frame = audio_file.tags['TDRC']
                if tdrc_frame.text and any(str(text).strip() for text in tdrc_frame.text):
                    return False
            
            # Check for TYER frame (Year) - ID3v2.3 and earlier
            if 'TYER' in audio_file.tags:
                tyer_frame = audio_file.tags['TYER']
                if tyer_frame.text and any(str(text).strip() for text in tyer_frame.text):
                    return False
            
            return True
            
        except (AttributeError, KeyError):
            return True
    
    def add_missing_tags(
        self,
        audio_file: MP3,
        file_path: Path,
        genre: Optional[str] = None,
        year: Optional[str] = None,
    ) -> List[str]:
        """Add missing genre and year tags to the MP3 file.
        
        Args:
            audio_file: MP3 object to modify.
            file_path: Path to the file (for error reporting).
            genre: Genre value to add if missing (optional).
            year: Year value to add if missing (optional).
            
        Returns:
            List of tag names that were added.
        """
        added_tags = []

        # Preserve whether values were provided explicitly
        provided_genre = genre is not None
        provided_year = year is not None

        if genre is None:
            genre = self.config.default_genre
        if year is None:
            year = self.config.default_year

        try:
            # Add genre tag if needed and provided
            if genre and self.needs_genre_tag(audio_file):
                if provided_genre:
                    self._add_genre_tag(audio_file, genre)
                else:
                    self._add_genre_tag(audio_file)
                added_tags.append('genre')

            # Add year tag if needed and provided
            if year and self.needs_year_tag(audio_file):
                if provided_year:
                    self._add_year_tag(audio_file, year)
                else:
                    self._add_year_tag(audio_file)
                added_tags.append('year')
            
            # Save the file if any tags were added
            if added_tags:
                self._save_file_safely(audio_file, file_path)
            
            return added_tags
            
        except Exception as e:
            raise Exception(f"Failed to add tags: {str(e)}")
    
    def _add_genre_tag(self, audio_file: MP3, genre: Optional[str] = None) -> None:
        """Add genre tag to the MP3 file.

        Args:
            audio_file: MP3 object to modify.
            genre: Genre value to add. If None, uses default from configuration.
        """
        if genre is None:
            genre = self.config.default_genre
        # Use TCON frame for genre
        audio_file.tags['TCON'] = TCON(encoding=3, text=[genre])
    
    def _add_year_tag(self, audio_file: MP3, year: Optional[str] = None) -> None:
        """Add year tag to the MP3 file.

        Args:
            audio_file: MP3 object to modify.
            year: Year value to add. If None, uses default from configuration.
        """
        if year is None:
            year = self.config.default_year
        # Add TDRC frame (Recording Date) - ID3v2.4
        audio_file.tags['TDRC'] = TDRC(encoding=3, text=[year])
        
        # Also add TYER frame for backward compatibility with ID3v2.3
        audio_file.tags['TYER'] = TYER(encoding=3, text=[year])
    
    def _save_file_safely(self, audio_file: MP3, file_path: Path) -> None:
        """Save the MP3 file safely with comprehensive error handling.
        
        Args:
            audio_file: MP3 object to save.
            file_path: Path to the file.
        """
        # Skip saving in dry-run mode
        if self.dry_run:
            return
        
        try:
            # Check if file is writable before attempting to save
            if not file_path.exists():
                raise Exception("File no longer exists")
            
            # Check file permissions
            if not file_path.is_file():
                raise Exception("Path is not a file")
            
            # Try to save the file
            audio_file.save()
            
        except PermissionError:
            raise Exception(f"Permission denied - cannot write to file {file_path}")
        except OSError as e:
            if e.errno == 28:  # No space left on device
                raise Exception(f"No space left on device when saving {file_path}")
            elif e.errno == 13:  # Permission denied
                raise Exception(f"Permission denied when saving {file_path}")
            else:
                raise Exception(f"OS error when saving {file_path}: {str(e)}")
        except mutagen.MutagenError as e:
            raise Exception(f"Mutagen error when saving {file_path}: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error when saving {file_path}: {str(e)}")
    
    def is_supported_file(self, file_path: Path) -> bool:
        """Check if the file is a supported MP3 file format.
        
        Args:
            file_path: Path to the file to check.
            
        Returns:
            True if the file is supported, False otherwise.
        """
        try:
            # Check file extension first
            if not file_path.suffix.lower() == '.mp3':
                return False
            
            # Try to load the file to verify it's a valid MP3
            audio_file = self._load_mp3_file(file_path)
            return audio_file is not None
            
        except Exception:
            return False
    
    def get_file_error_info(self, file_path: Path) -> str:
        """Get detailed error information about why a file cannot be processed.
        
        Args:
            file_path: Path to the file to analyze.
            
        Returns:
            String describing the specific error or issue.
        """
        try:
            # Check basic file properties
            if not file_path.exists():
                return "File does not exist"
            
            if not file_path.is_file():
                return "Path is not a regular file"
            
            if file_path.stat().st_size == 0:
                return "File is empty"
            
            if not file_path.suffix.lower() == '.mp3':
                return f"Unsupported file extension: {file_path.suffix}"
            
            # Try to load with Mutagen and get specific error
            try:
                audio_file = MP3(str(file_path))
                if audio_file.info is None:
                    return "File has no audio information (possibly corrupted)"
                
                if not hasattr(audio_file.info, 'length') or audio_file.info.length <= 0:
                    return "File has invalid audio length (possibly corrupted)"
                
                return "File appears to be valid"
                
            except mutagen.mp3.HeaderNotFoundError:
                return "MP3 header not found (corrupted or not an MP3 file)"
            except mutagen.id3.ID3NoHeaderError:
                return "No ID3 header found (valid MP3 but no metadata)"
            except mutagen.MutagenError as e:
                return f"Mutagen parsing error: {str(e)}"
            
        except PermissionError:
            return "Permission denied - cannot read file"
        except OSError as e:
            return f"OS error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    def get_existing_tags(self, file_path: Path) -> dict:
        """Get existing tags from an MP3 file for inspection.
        
        Args:
            file_path: Path to the MP3 file.
            
        Returns:
            Dictionary containing existing tag information.
        """
        try:
            audio_file = self._load_mp3_file(file_path)
            if audio_file is None:
                return {}
            
            tags_info = {}
            
            # Check genre
            if 'TCON' in audio_file.tags:
                genre_frame = audio_file.tags['TCON']
                tags_info['genre'] = [str(text) for text in genre_frame.text]
            
            # Check year (TDRC first, then TYER)
            if 'TDRC' in audio_file.tags:
                tdrc_frame = audio_file.tags['TDRC']
                tags_info['year_tdrc'] = [str(text) for text in tdrc_frame.text]
            
            if 'TYER' in audio_file.tags:
                tyer_frame = audio_file.tags['TYER']
                tags_info['year_tyer'] = [str(text) for text in tyer_frame.text]
            
            return tags_info
            
        except Exception:
            return {}