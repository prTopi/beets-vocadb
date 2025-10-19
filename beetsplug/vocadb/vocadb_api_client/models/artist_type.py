from enum import auto

from beetsplug.vocadb.vocadb_api_client.models import PascalCaseStrEnum


class ArtistType(PascalCaseStrEnum):
    # Vocalist
    VOCALOID = auto()
    UTAU = "UTAU"
    CEVIO = "CeVIO"
    SYNTHESIZER_V = auto()
    NEUTRINO = "NEUTRINO"
    VOI_SONA = auto()
    NEW_TYPE = auto()
    VOICEROID = auto()
    VOICEVOX = "VOICEVOX"
    AIVOICE = "AIVOICE"
    A_C_E_VIRTUAL_SINGER = auto()
    OTHER_VOICE_SYNTHESIZER = auto()
    OTHER_VOCALIST = auto()

    # Producer
    PRODUCER = auto()
    COVER_ARTIST = auto()
    ANIMATOR = auto()
    ILLUSTRATOR = auto()

    # Group
    CIRCLE = auto()
    LABEL = auto()
    OTHER_GROUP = auto()

    # UtaiteDB-specific
    BAND = auto()
    UTAITE = auto()
    UNKNOWN = auto()

    # TouhouDB-specific
    VOCALIST = auto()
    CHARACTER = auto()
    DESIGNER = auto()

    # Other
    LYRICIST = auto()
    INSTRUMENTALIST = auto()
    OTHER_INDIVIDUAL = auto()
