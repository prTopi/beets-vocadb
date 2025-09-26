from beetsplug.vocadb.vocadb_api_client.models import StrEnum


class SongType(StrEnum):
    UNSPECIFIED = "Unspecified"
    ORIGINAL = "Original"
    REMASTER = "Remaster"
    REMIX = "Remix"
    COVER = "Cover"
    ARRANGEMENT = "Arrangement"
    INSTRUMENTAL = "Instrumental"
    MASHUP = "Mashup"
    SHORTVERSION = "ShortVersion"
    MUSICPV = "MusicPV"
    DRAMAPV = "DramaPV"
    LIVE = "Live"
    ILLUSTRATION = "Illustration"
    OTHER = "Other"

    # TouhouDB-specific
    REARRANGEMENT = "Rearrangement"
