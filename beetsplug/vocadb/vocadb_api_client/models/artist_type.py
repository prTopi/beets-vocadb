from beetsplug.vocadb.vocadb_api_client.models import StrEnum


class ArtistType(StrEnum):
    # Vocalist
    VOCALOID = "Vocaloid"
    UTAU = "UTAU"
    CEVIO = "CeVIO"
    SYNTHESIZERV = "SynthesizerV"
    NEUTRINO = "NEUTRINO"
    VOISONA = "VoiSona"
    NEWTYPE = "NewType"
    VOICEROID = "Voiceroid"
    VOICEVOX = "VOICEVOX"
    AIVOICE = "AIVOICE"
    ACEVIRTUALSINGER = "ACEVirtualSinger"
    OTHERVOICESYNTHESIZER = "OtherVoiceSynthesizer"
    OTHERVOCALIST = "OtherVocalist"

    # Producer
    MUSICPRODUCER = "Producer"
    COVERARTIST = "CoverArtist"
    ANIMATIONPRODUCER = "Animator"
    ILLUSTRATOR = "Illustrator"

    # Group
    CIRCLE = "Circle"
    LABEL = "Label"
    OTHERGROUP = "OtherGroup"

    # UtaiteDB-specific
    BAND = "Band"
    UTAITE = "Utaite"
    UNKNOWN = "Unknown"

    # TouhouDB-specific
    VOCALIST = "Vocalist"
    CHARACTER = "Character"
    DESIGNER = "Designer"

    # Other
    LYRICIST = "Lyricist"
    INSTRUMENTALIST = "Instrumentalist"
    OTHERINDIVIDUAL = "OtherIndividual"
