from __future__ import annotations

from enum import auto
from functools import cache

from . import PascalCaseStrEnum


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

    @classmethod
    @cache
    def any_vocal_synth(cls) -> set[ArtistType]:
        return {
            cls.VOCALOID,
            cls.UTAU,
            cls.CEVIO,
            cls.SYNTHESIZER_V,
            cls.NEUTRINO,
            cls.VOI_SONA,
            cls.NEW_TYPE,
            cls.VOICEROID,
            cls.VOICEVOX,
            cls.AIVOICE,
            cls.A_C_E_VIRTUAL_SINGER,
            cls.OTHER_VOICE_SYNTHESIZER,
            cls.OTHER_VOCALIST,
        }
