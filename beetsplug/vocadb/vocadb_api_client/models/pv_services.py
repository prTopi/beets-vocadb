import sys

from beetsplug.vocadb.vocadb_api_client.models import StrEnum, StrEnumSet

if not sys.version_info < (3, 10):
    from typing import TypeAlias  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import TypeAlias


class PVServices(StrEnum):
    NOTHING = "Nothing"
    NICONICODOUGA = "NicoNicoDouga"
    YOUTUBE = "Youtube"
    SOUNDCLOUD = "SoundCloud"
    VIMEO = "Vimeo"
    PIAPRO = "Piapro"
    BILIBILI = "Bilibili"
    FILE = "File"
    LOCALFILE = "LocalFile"
    CREOFUGA = "Creofuga"
    BANDCAMP = "Bandcamp"


PVServicesSet: TypeAlias = StrEnumSet[PVServices]
