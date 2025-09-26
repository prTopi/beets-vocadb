from beetsplug.vocadb.vocadb_api_client.models import StrEnum

# TODO: decide


class ArtistRoles(StrEnum):
    DEFAULT = "Default"
    ANIMATOR = "Animator"
    ARRANGER = "Arranger"
    COMPOSER = "Composer"
    DISTRIBUTOR = "Distributor"
    ILLUSTRATOR = "Illustrator"
    INSTRUMENTALIST = "Instrumentalist"
    LYRICIST = "Lyricist"
    MASTERING = "Mastering"
    MIXER = "Mixer"
    OTHER = "Other"
    PUBLISHER = "Publisher"
    VOCALDATAPROVIDER = "VocalDataProvider"
    VOCALIST = "Vocalist"
    VOICEMANIPULATOR = "VoiceManipulator"

    # UtaiteDB- and TouhouDB-specific
    CHORUS = "Chorus"

    # UtaiteDB-specific
    ENCODER = "Encoder"
