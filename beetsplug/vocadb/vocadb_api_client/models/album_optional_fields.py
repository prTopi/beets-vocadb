import sys

from beetsplug.vocadb.vocadb_api_client.models import StrEnum, StrEnumSet

if not sys.version_info < (3, 10):
    from typing import TypeAlias  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import TypeAlias


class AlbumOptionalFields(StrEnum):
    NONE = "None"
    ADDITIONALNAMES = "AdditionalNames"
    ARTISTS = "Artists"
    DESCRIPTION = "Description"
    DISCS = "Discs"
    IDENTIFIERS = "Identifiers"
    MAINPICTURE = "MainPicture"
    NAMES = "Names"
    PVS = "PVs"
    RELEASEEVENT = "ReleaseEvent"
    TAGS = "Tags"
    TRACKS = "Tracks"
    WEBLINKS = "WebLinks"


AlbumOptionalFieldsSet: TypeAlias = StrEnumSet[AlbumOptionalFields]
