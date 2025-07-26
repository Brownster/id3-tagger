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
    source: str = "musicbrainz"

    def has_genre(self) -> bool:
        """Check if genre information is available."""
        return self.genre is not None and self.genre.strip() != ""

class MusicBrainzClient:
    """Simple client for querying MusicBrainz for genre information."""

    def __init__(self, app_name: str = "mp3-id3-processor", app_version: str = "1.0", contact: Optional[str] = None):
        """Initialize the client and set the user agent."""
        self.app_name = app_name
        self.app_version = app_version
        self.contact = contact or ""
        musicbrainzngs.set_useragent(self.app_name, self.app_version, self.contact)

    def get_genre(self, artist: str, album: str, track: str) -> Optional[MusicBrainzMetadata]:
        """Fetch genre for the given artist/album/track combination."""
        if not (artist and album and track):
            return None
        try:
            result = musicbrainzngs.search_recordings(artist=artist, release=album, recording=track, limit=1)
            recordings = result.get("recording-list")
            if recordings:
                recording = recordings[0]
                tag_list = recording.get("tag-list", [])
                for tag in tag_list:
                    if int(tag.get("count", 0)) > 0:
                        name = tag.get("name")
                        if name:
                            return MusicBrainzMetadata(
                                artist=artist,
                                album=album,
                                track=track,
                                genre=name.capitalize(),
                            )
        except musicbrainzngs.WebServiceError as exc:
            logger.warning(f"MusicBrainz error: {exc}")
        except Exception as exc:
            logger.debug(f"Unexpected MusicBrainz error: {exc}")
        return None
