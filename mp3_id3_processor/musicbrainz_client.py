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
            result = musicbrainzngs.search_recordings(
                artist=artist,
                release=album,
                recording=track,
                limit=1,
                includes=["tags", "releases"],
            )
            recordings = result.get("recording-list")
            if not recordings:
                return None

            recording = recordings[0]

            genre = None
            tag_list = recording.get("tag-list", [])
            for tag in tag_list:
                if int(tag.get("count", 0)) > 0:
                    name = tag.get("name")
                    if name:
                        genre = name.capitalize()
                        break

            year = None
            release_list = recording.get("release-list", [])
            if release_list:
                date_str = release_list[0].get("date")
                if date_str and len(date_str) >= 4 and date_str[:4].isdigit():
                    year = date_str[:4]

            return MusicBrainzMetadata(
                artist=artist,
                album=album,
                track=track,
                genre=genre,
                year=year,
            )
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
