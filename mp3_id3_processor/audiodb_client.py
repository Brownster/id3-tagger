"""TheAudioDB API client for fetching music metadata."""

import json
import time
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from urllib.parse import quote
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import logging

logger = logging.getLogger(__name__)


@dataclass
class AudioDBMetadata:
    """Container for metadata retrieved from TheAudioDB API."""
    artist: Optional[str] = None
    album: Optional[str] = None
    track: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[str] = None
    source: str = "audiodb"
    
    def has_genre(self) -> bool:
        """Check if genre information is available."""
        return self.genre is not None and self.genre.strip() != ""
    
    def has_year(self) -> bool:
        """Check if year information is available."""
        return self.year is not None and self.year.strip() != ""
    
    def has_useful_data(self) -> bool:
        """Check if this metadata contains useful information."""
        return self.has_genre() or self.has_year()


class AudioDBClient:
    """Client for TheAudioDB API with caching and rate limiting."""
    
    BASE_URL = "https://www.theaudiodb.com/api/v1/json/2"
    
    def __init__(self, cache_dir: Optional[Path] = None, request_delay: float = 0.5):
        """Initialize the AudioDB client.
        
        Args:
            cache_dir: Directory for caching API responses. If None, uses temp directory.
            request_delay: Delay between API requests in seconds to respect rate limits.
        """
        self.request_delay = request_delay
        self.last_request_time = 0.0
        
        # Set up cache directory
        if cache_dir is None:
            cache_dir = Path.home() / ".mp3_id3_processor" / "cache"
        
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"AudioDB client initialized with cache dir: {self.cache_dir}")
    
    def search_artist(self, artist_name: str) -> Optional[AudioDBMetadata]:
        """Search for artist information.
        
        Args:
            artist_name: Name of the artist to search for.
            
        Returns:
            AudioDBMetadata if found, None otherwise.
        """
        if not artist_name or not artist_name.strip():
            return None
        
        try:
            # Clean and encode artist name
            clean_artist = artist_name.strip()
            encoded_artist = quote(clean_artist)
            
            url = f"{self.BASE_URL}/search.php?s={encoded_artist}"
            data = self._make_request(url, f"artist_{clean_artist}")
            
            if data and 'artists' in data and data['artists']:
                artist_data = data['artists'][0]  # Take first match
                
                # Extract genre from artist data
                genre = self._extract_genre_from_artist(artist_data)
                
                return AudioDBMetadata(
                    artist=clean_artist,
                    genre=genre,
                    source="audiodb_artist"
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Error searching for artist '{artist_name}': {e}")
            return None
    
    def search_album(self, artist_name: str, album_name: str) -> Optional[AudioDBMetadata]:
        """Search for album information.
        
        Args:
            artist_name: Name of the artist.
            album_name: Name of the album.
            
        Returns:
            AudioDBMetadata if found, None otherwise.
        """
        if not artist_name or not album_name:
            return None
        
        try:
            clean_artist = artist_name.strip()
            clean_album = album_name.strip()
            encoded_artist = quote(clean_artist)
            encoded_album = quote(clean_album)
            
            url = f"{self.BASE_URL}/searchalbum.php?s={encoded_artist}&a={encoded_album}"
            data = self._make_request(url, f"album_{clean_artist}_{clean_album}")
            
            if data and 'album' in data and data['album']:
                album_data = data['album'][0]  # Take first match
                
                # Extract genre and year from album data
                genre = self._extract_genre_from_album(album_data)
                year = self._extract_year_from_album(album_data)
                
                return AudioDBMetadata(
                    artist=clean_artist,
                    album=clean_album,
                    genre=genre,
                    year=year,
                    source="audiodb_album"
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Error searching for album '{artist_name} - {album_name}': {e}")
            return None
    
    def search_track(self, artist_name: str, track_name: str) -> Optional[AudioDBMetadata]:
        """Search for track information.
        
        Args:
            artist_name: Name of the artist.
            track_name: Name of the track.
            
        Returns:
            AudioDBMetadata if found, None otherwise.
        """
        if not artist_name or not track_name:
            return None
        
        try:
            clean_artist = artist_name.strip()
            clean_track = track_name.strip()
            encoded_artist = quote(clean_artist)
            encoded_track = quote(clean_track)
            
            url = f"{self.BASE_URL}/track.php?h={encoded_artist}&t={encoded_track}"
            data = self._make_request(url, f"track_{clean_artist}_{clean_track}")
            
            if data and 'track' in data and data['track']:
                track_data = data['track'][0]  # Take first match
                
                # Extract album and year from track data
                album = self._extract_album_from_track(track_data)
                year = self._extract_year_from_track(track_data)
                
                # If we have album info, try to get more metadata from album search
                if album:
                    album_metadata = self.search_album(clean_artist, album)
                    if album_metadata and album_metadata.has_useful_data():
                        album_metadata.track = clean_track
                        return album_metadata
                
                return AudioDBMetadata(
                    artist=clean_artist,
                    track=clean_track,
                    album=album,
                    year=year,
                    source="audiodb_track"
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Error searching for track '{artist_name} - {track_name}': {e}")
            return None
    
    def _make_request(self, url: str, cache_key: str) -> Optional[Dict[str, Any]]:
        """Make an HTTP request with caching and rate limiting.
        
        Args:
            url: URL to request.
            cache_key: Key for caching the response.
            
        Returns:
            Parsed JSON response or None if request failed.
        """
        # Check cache first
        cached_data = self._get_cached_response(cache_key)
        if cached_data is not None:
            logger.debug(f"Using cached response for: {cache_key}")
            return cached_data
        
        # Rate limiting
        self._wait_for_rate_limit()
        
        try:
            logger.debug(f"Making API request to: {url}")
            
            # Create request with user agent
            request = Request(url)
            request.add_header('User-Agent', 'MP3-ID3-Processor/1.0')
            
            # Make the request
            with urlopen(request, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    
                    # Cache the response
                    self._cache_response(cache_key, data)
                    
                    return data
                else:
                    logger.warning(f"API request failed with status {response.status}: {url}")
                    return None
        
        except HTTPError as e:
            logger.warning(f"HTTP error for {url}: {e}")
            return None
        except URLError as e:
            logger.warning(f"URL error for {url}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error for {url}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error for {url}: {e}")
            return None
    
    def _wait_for_rate_limit(self):
        """Wait to respect rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_cache_key_hash(self, cache_key: str) -> str:
        """Generate a hash for the cache key to create a safe filename."""
        return hashlib.md5(cache_key.encode('utf-8')).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired.
        
        Args:
            cache_key: Key for the cached response.
            
        Returns:
            Cached data or None if not available/expired.
        """
        try:
            cache_file = self.cache_dir / f"{self._get_cache_key_hash(cache_key)}.json"
            
            if not cache_file.exists():
                return None
            
            # Check if cache is too old (24 hours)
            cache_age = time.time() - cache_file.stat().st_mtime
            if cache_age > 24 * 60 * 60:  # 24 hours in seconds
                logger.debug(f"Cache expired for: {cache_key}")
                cache_file.unlink()  # Delete expired cache
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        except Exception as e:
            logger.debug(f"Error reading cache for {cache_key}: {e}")
            return None
    
    def _cache_response(self, cache_key: str, data: Dict[str, Any]):
        """Cache API response.
        
        Args:
            cache_key: Key for caching.
            data: Data to cache.
        """
        try:
            cache_file = self.cache_dir / f"{self._get_cache_key_hash(cache_key)}.json"
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Cached response for: {cache_key}")
        
        except Exception as e:
            logger.debug(f"Error caching response for {cache_key}: {e}")
    
    def _extract_genre_from_artist(self, artist_data: Dict[str, Any]) -> Optional[str]:
        """Extract genre from artist data."""
        try:
            # TheAudioDB provides genre in strGenre field
            genre = artist_data.get('strGenre')
            if genre and genre.strip():
                return genre.strip()
            
            # Fallback to style
            style = artist_data.get('strStyle')
            if style and style.strip():
                return style.strip()
            
            return None
        
        except Exception:
            return None
    
    def _extract_genre_from_album(self, album_data: Dict[str, Any]) -> Optional[str]:
        """Extract genre from album data."""
        try:
            # TheAudioDB provides genre in strGenre field
            genre = album_data.get('strGenre')
            if genre and genre.strip():
                return genre.strip()
            
            # Fallback to style
            style = album_data.get('strStyle')
            if style and style.strip():
                return style.strip()
            
            return None
        
        except Exception:
            return None
    
    def _extract_year_from_album(self, album_data: Dict[str, Any]) -> Optional[str]:
        """Extract year from album data."""
        try:
            # TheAudioDB provides release date in intYearReleased
            year = album_data.get('intYearReleased')
            if year:
                year_str = str(year).strip()
                if year_str.isdigit() and 1900 <= int(year_str) <= 2030:
                    return year_str
            
            return None
        
        except Exception:
            return None
    
    def _extract_album_from_track(self, track_data: Dict[str, Any]) -> Optional[str]:
        """Extract album name from track data."""
        try:
            album = track_data.get('strAlbum')
            if album and album.strip():
                return album.strip()
            
            return None
        
        except Exception:
            return None
    
    def _extract_year_from_track(self, track_data: Dict[str, Any]) -> Optional[str]:
        """Extract year from track data."""
        try:
            # Track data might have year information
            year = track_data.get('intYearReleased')
            if year:
                year_str = str(year).strip()
                if year_str.isdigit() and 1900 <= int(year_str) <= 2030:
                    return year_str
            
            return None
        
        except Exception:
            return None
    
    def clear_cache(self):
        """Clear all cached responses."""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics.
        """
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                'cache_dir': str(self.cache_dir),
                'cached_responses': len(cache_files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
        
        except Exception as e:
            logger.warning(f"Error getting cache stats: {e}")
            return {'error': str(e)}