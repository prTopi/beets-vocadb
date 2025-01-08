"""Attrs classes related to API requests"""

from __future__ import annotations
from datetime import datetime
import re
from typing import Optional

import msgspec

from . import StrEnum


class TaggedBase(
    msgspec.Struct, omit_defaults=True, rename="camel"
): ...


class FrozenBase(
    msgspec.Struct,
    frozen=True,
    forbid_unknown_fields=True,
    omit_defaults=True,
    rename="camel",
): ...


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


class EntryStatus(StrEnum):
    DRAFT = "Draft"
    FINISHED = "Finished"
    APPROVED = "Approved"
    LOCKED = "Locked"


class Artist(TaggedBase):
    additional_names: str
    artist_type: ArtistType
    deleted: bool
    id: int
    name: str
    status: EntryStatus
    version: int
    release_date: Optional[datetime] = None
    picture_mime: Optional[str] = None


class ArtistCategories(StrEnum):
    VOCALIST = "Vocalist"
    NOTHING = "Nothing"
    PRODUCER = "Producer"
    ANIMATOR = "Animator"
    LABEL = "Label"
    CIRCLE = "Circle"
    OTHER = "Other"
    BAND = "Band"
    ILLUSTRATOR = "Illustrator"
    SUBJECT = "Subject"


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


# to avoid extra whitespace
SPLIT_PATTERN: re.Pattern[str] = re.compile(r"\s*,\s*")


class AlbumArtist(TaggedBase, kw_only=True):
    _categories: str = msgspec.field(name="categories")
    _effective_roles: str = msgspec.field(name="effectiveRoles")
    is_support: bool
    name: str
    roles: str
    artist: Optional[Artist] = None
    categories: set[ArtistCategories] = msgspec.field(
        default_factory=set, name="dummy1"
    )
    effective_roles: set[ArtistRoles] = msgspec.field(
        default_factory=set, name="dummy2"
    )

    def __post_init__(self) -> None:
        self.categories = {
            ArtistCategories(c) for c in SPLIT_PATTERN.split(self._categories) if c
        }
        self.effective_roles = {
            ArtistRoles(r) for r in SPLIT_PATTERN.split(self._effective_roles) if r
        }


class SongArtist(AlbumArtist):
    id: int
    is_custom_name: bool


class Tag(FrozenBase, frozen=True):
    name: str
    additional_names: Optional[str] = None
    category_name: Optional[str] = None
    id: Optional[int] = None
    url_slug: Optional[str] = None


class TagUsage(TaggedBase):
    count: int
    tag: Tag


class ContentLanguageSelection(StrEnum):
    UNSPECIFIED = "Unspecified"
    JAPANESE = "Japanese"
    ROMAJI = "Romaji"
    ENGLISH = "English"


class AlbumOrSong(TaggedBase):
    """Base class with attributes shared by Album and Song"""

    artist_string: str
    create_date: str
    default_name: str
    default_name_language: ContentLanguageSelection
    id: int
    name: str
    status: EntryStatus


class TranslationType(StrEnum):
    ORIGINAL = "Original"
    ROMANIZED = "Romanized"
    TRANSLATION = "Translation"


class Lyrics(TaggedBase):
    translation_type: TranslationType
    value: str
    culture_codes: set[str]
    id: Optional[int] = None
    source: Optional[str] = None
    url: Optional[str] = None


class DiscMediaType(StrEnum):
    AUDIO = "Audio"
    VIDEO = "Video"


class Disc(TaggedBase):
    disc_number: int
    media_type: DiscMediaType
    name: str
    total: Optional[int] = None
    id: Optional[int] = None


class ReleaseDate(TaggedBase):
    is_empty: bool
    day: Optional[int] = None
    month: Optional[int] = None
    year: Optional[int] = None


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


class SongType(StrEnum):
    UNSPECIFIED = "Unspecified"
    ORIGINAL = "Original"
    REMASTER = "Remaster"
    REMIX = "Remix"
    COVER = "Cover"
    ARRANGEMENT = "Arrangement"
    INSTRUMENTAL = "Instrumental"
    MASHUP = "Mashup"
    MUSICPV = "MusicPV"
    DRAMAPV = "DramaPV"
    LIVE = "Live"
    ILLUSTRATION = "Illustration"
    OTHER = "Other"

    # TouhouDB-specific
    REARRANGEMENT = "Rearrangement"


class Song(AlbumOrSong):
    artists: list[SongArtist]
    culture_codes: set[str]
    favorited_times: int
    length_seconds: float
    lyrics: list[Lyrics]
    pv_services: str
    rating_score: int
    song_type: SongType
    tags: list[TagUsage]
    version: int
    original_version_id: Optional[int] = None
    max_milli_bpm: Optional[int] = None
    min_milli_bpm: Optional[int] = None
    publish_date: Optional[datetime] = None


class SongInAlbum(TaggedBase):
    disc_number: int
    track_number: int
    computed_culture_codes: set[str]
    id: Optional[int] = None
    name: Optional[str] = None
    song: Optional[Song] = None


class WebLinkCategory(StrEnum):
    OFFICIAL = "Official"
    COMMERCIAL = "Commercial"
    REFERENCE = "Reference"
    OTHER = "Other"


class WebLink(TaggedBase):
    category: WebLinkCategory
    description: str
    disabled: bool
    url: str
    description_or_url: Optional[str] = None
    id: Optional[int] = None


class DiscTypes(StrEnum):
    UNKNOWN = "Unknown"
    ALBUM = "Album"
    SINGLE = "Single"
    EP = "EP"
    SPLITALBUM = "SplitAlbum"
    COMPILATION = "Compilation"
    VIDEO = "Video"
    ARTBOOK = "Artbook"
    GAME = "Game"
    FANMADE = "Fanmade"
    INSTRUMENTAL = "Instrumental"
    OTHER = "Other"


class AlbumFromQuery(AlbumOrSong):
    release_date: ReleaseDate
    disc_type: DiscTypes


class Album(AlbumFromQuery):
    artists: list[AlbumArtist]
    rating_average: float
    rating_count: int
    tags: list[TagUsage]
    tracks: list[SongInAlbum]
    version: int
    web_links: list[WebLink]
    discs: list[Disc]
    catalog_number: Optional[str] = None


class BaseQueryResult(TaggedBase):
    term: str
    total_count: int


class SongQueryResult(BaseQueryResult):
    items: list[Song]


class AlbumQueryResult(BaseQueryResult):
    items: list[AlbumFromQuery]
