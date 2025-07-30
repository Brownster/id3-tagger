import musicbrainzngs
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class MusicBrainzMetadata:
    """Container for metadata retrieved from MusicBrainz."""
    artist: Optional[str] = None
    album: Optional[str] = None
    track: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[str] = None
    source: str = "musicbrainz"

    def has_genre(self) -> bool:
        """Check if genre information is available."""
        return self.genre is not None and self.genre.strip() != ""

    def has_year(self) -> bool:
        """Check if year information is available."""
        return self.year is not None and self.year.strip() != ""

class MusicBrainzClient:
    """Simple client for querying MusicBrainz for metadata."""

    def __init__(
        self,
        app_name: str = "mp3-id3-processor",
        app_version: str = "1.0",
        contact: Optional[str] = "https://example.com",
        use_original_release_date: bool = True,
    ):
        """Initialize the client and configure request settings.
        
        Args:
            app_name: Application name for MusicBrainz user agent.
            app_version: Application version for MusicBrainz user agent.
            contact: Contact information for MusicBrainz user agent.
            use_original_release_date: If True, prefer original release dates from 
                release-groups. If False, use earliest release date from any release.
        """
        self.app_name = app_name
        self.app_version = app_version
        self.contact = contact or "https://example.com"
        self.use_original_release_date = use_original_release_date

        musicbrainzngs.set_useragent(self.app_name, self.app_version, self.contact)
        # Follow MusicBrainz guidelines: limit one request per second
        musicbrainzngs.set_rate_limit(limit_or_interval=1.0, new_requests=1)

    def get_metadata(
        self, artist: str, album: str, track: str
    ) -> Optional[MusicBrainzMetadata]:
        """Fetch genre and year for the given artist/album/track."""
        if not (artist and album and track):
            return None

        try:
            logger.debug(f"Searching for: artist='{artist}', album='{album}', track='{track}'")
            
            # Step 1: Search for recordings to find the recording ID
            search_result = musicbrainzngs.search_recordings(
                artist=artist,
                release=album,
                recording=track,
                limit=1
            )
            
            recordings = search_result.get("recording-list")
            if not recordings:
                logger.debug("No recordings found in search")
                return None

            recording_id = recordings[0]["id"]
            logger.debug(f"Found recording ID: {recording_id}")
            
            # Step 2: Get detailed recording information with tags and releases
            recording_data = musicbrainzngs.get_recording_by_id(
                recording_id,
                includes=["tags", "releases"]
            )
            
            recording = recording_data["recording"]

            # Extract genre from tags
            genre = None
            tag_list = recording.get("tag-list", [])
            if tag_list:
                # Sort tags by count and take the most popular one
                sorted_tags = sorted(tag_list, key=lambda x: int(x.get("count", 0)), reverse=True)
                for tag in sorted_tags:
                    if int(tag.get("count", 0)) > 0:
                        name = tag.get("name")
                        if name:
                            genre = name.capitalize()
                            logger.debug(f"Found genre from tag: {genre}")
                            break

            # Extract year using the configured approach
            year = None
            if self.use_original_release_date:
                year = self._get_original_release_year(recording)
            else:
                year = self._get_earliest_release_year(recording)
            
            if year:
                logger.debug(f"Found year: {year} (using {'original' if self.use_original_release_date else 'earliest'} release date approach)")

            # If no genre found from recording tags, try to get it from release-group
            if not genre:
                release_list = recording.get("release-list", [])
                for release in release_list:
                    release_id = release.get("id")
                    if release_id:
                        try:
                            # Get release with release-group information
                            release_data = musicbrainzngs.get_release_by_id(
                                release_id,
                                includes=["release-groups"]
                            )
                            
                            release_group = release_data.get("release", {}).get("release-group")
                            if release_group:
                                rg_id = release_group["id"]
                                logger.debug(f"Getting tags for release-group: {rg_id}")
                                
                                # Get release group with tags
                                rg_data = musicbrainzngs.get_release_group_by_id(
                                    rg_id,
                                    includes=["tags"]
                                )
                                
                                rg_tags = rg_data.get("release-group", {}).get("tag-list", [])
                                if rg_tags:
                                    # Sort tags by count and take the most popular one
                                    sorted_rg_tags = sorted(rg_tags, key=lambda x: int(x.get("count", 0)), reverse=True)
                                    for tag in sorted_rg_tags:
                                        if int(tag.get("count", 0)) > 0:
                                            name = tag.get("name")
                                            if name:
                                                # Convert to title case for consistency
                                                genre = name.title()
                                                logger.debug(f"Found genre from release-group: {genre} (count: {tag.get('count')})")
                                                break
                                    if genre:
                                        break
                        except Exception as e:
                            logger.debug(f"Error getting release-group tags: {e}")
                            continue

            result = MusicBrainzMetadata(
                artist=artist,
                album=album,
                track=track,
                genre=genre,
                year=year,
            )
            
            logger.debug(f"Final metadata: genre={genre}, year={year}")
            return result
            
        except musicbrainzngs.WebServiceError as exc:
            logger.warning(f"MusicBrainz error: {exc}")
        except Exception as exc:
            logger.debug(f"Unexpected MusicBrainz error: {exc}")
        return None

    def get_genre(self, artist: str, album: str, track: str) -> Optional[MusicBrainzMetadata]:
        """Compatibility wrapper returning only genre information."""
        metadata = self.get_metadata(artist, album, track)
        if metadata and metadata.genre:
            return metadata
        return None

    def _get_earliest_release_year(self, recording: dict) -> Optional[str]:
        """Get the earliest release year from any release (current behavior).
        
        Args:
            recording: Recording data from MusicBrainz.
            
        Returns:
            Year string if found, None otherwise.
        """
        release_list = recording.get("release-list", [])
        if not release_list:
            return None
        
        earliest_date = None
        for release in release_list:
            date_str = release.get("date")
            if date_str and len(date_str) >= 4 and date_str[:4].isdigit():
                if not earliest_date or date_str < earliest_date:
                    earliest_date = date_str
        
        return earliest_date[:4] if earliest_date else None

    def _get_original_release_year(self, recording: dict) -> Optional[str]:
        """Get the original release year from release-groups (new behavior).
        
        Args:
            recording: Recording data from MusicBrainz.
            
        Returns:
            Year string if found, None otherwise.
        """
        release_list = recording.get("release-list", [])
        if not release_list:
            return None
        
        # Collect unique release-group IDs by getting release details
        release_group_ids = set()
        for release in release_list[:5]:  # Limit to first 5 releases to avoid too many API calls
            release_id = release.get("id")
            if release_id:
                try:
                    # Get release details with release-group information
                    release_data = musicbrainzngs.get_release_by_id(
                        release_id,
                        includes=["release-groups"]
                    )
                    
                    release_info = release_data["release"]
                    release_group = release_info.get("release-group")
                    if release_group:
                        rg_id = release_group.get("id")
                        if rg_id:
                            release_group_ids.add(rg_id)
                            logger.debug(f"Found release-group {rg_id} from release {release_id}")
                    
                except Exception as e:
                    logger.debug(f"Error getting release {release_id}: {e}")
                    continue
        
        if not release_group_ids:
            logger.debug("No release-groups found, falling back to earliest release date")
            return self._get_earliest_release_year(recording)
        
        # Get first-release-date from each release-group
        earliest_first_release = None
        for rg_id in release_group_ids:
            try:
                rg_data = musicbrainzngs.get_release_group_by_id(rg_id)
                rg_info = rg_data["release-group"]
                first_release_date = rg_info.get("first-release-date")
                
                if first_release_date and len(first_release_date) >= 4:
                    if not earliest_first_release or first_release_date < earliest_first_release:
                        earliest_first_release = first_release_date
                        
                logger.debug(f"Release-group {rg_id}: first-release-date = {first_release_date}")
                        
            except Exception as e:
                logger.debug(f"Error getting release-group {rg_id}: {e}")
                continue
        
        if earliest_first_release:
            return earliest_first_release[:4]
        else:
            logger.debug("No release-group dates found, falling back to earliest release date")
            return self._get_earliest_release_year(recording)
