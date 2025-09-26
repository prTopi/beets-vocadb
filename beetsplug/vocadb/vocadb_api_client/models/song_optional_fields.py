import sys

from beetsplug.vocadb.vocadb_api_client.models import StrEnum, StrEnumSet

if not sys.version_info < (3, 10):
    from typing import TypeAlias  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import TypeAlias


class SongOptionalFields(StrEnum):
    NONE = "None"
    ADDIATIONALNAMES = "AdditionalNames"
    ALBUMS = "Albums"
    ARTISTS = "Artists"
    LYRICS = "Lyrics"
    MAINPICTURE = "MainPicture"
    NAMES = "Names"
    PVS = "PVs"
    RELEASEEVENT = "ReleaseEvent"
    TAGS = "Tags"
    THUMBURL = "ThumbUrl"
    WEBLINKS = "WebLinks"
    BPM = "Bpm"
    CULTURECODES = "CultureCodes"


SongOptionalFieldsSet: TypeAlias = StrEnumSet[SongOptionalFields]
