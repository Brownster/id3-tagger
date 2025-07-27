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
    ):
        """Initialize the client and configure request settings."""
        self.app_name = app_name
        self.app_version = app_version
        self.contact = contact or "https://example.com"

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

            # Extract year from release dates
            year = None
            release_list = recording.get("release-list", [])
            if release_list:
                # Look for the earliest release date
                earliest_date = None
                for release in release_list:
                    date_str = release.get("date")
                    if date_str and len(date_str) >= 4 and date_str[:4].isdigit():
                        if not earliest_date or date_str < earliest_date:
                            earliest_date = date_str
                
                if earliest_date:
                    year = earliest_date[:4]
                    logger.debug(f"Found year from release: {year}")

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
