from __future__ import annotations

import sys
from functools import cached_property

from beets.library import Item

from .mapper import (
    AlbumFlexibleAttributes,
    FlexibleAttributes,
    ItemFlexibleAttributes,
    Mapper,
)
from .utils import get_language_preference

if not sys.version_info < (3, 12):
    from typing import override  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import override

from typing import TYPE_CHECKING, TypedDict

import httpx
from beets import __version__ as beets_version
from beets import config as beets_config
from beets import dbcore
from beets.autotag.distance import Distance
from beets.metadata_plugins import MetadataSourcePlugin
from beets.plugins import apply_item_changes
from beets.ui import (
    Subcommand,
    should_move,  # pyright: ignore[reportUnknownVariableType]
    should_write,  # pyright: ignore[reportUnknownVariableType]
    show_model_changes,
)

from .vocadb_api_client import (
    AlbumApiApi,
    AlbumOptionalFields,
    AlbumOptionalFieldsSet,
    ApiClient,
    ArtistApiApi,
    ContentLanguagePreference,
    NameMatchMode,
    SongApiApi,
    SongOptionalFields,
    SongOptionalFieldsSet,
    SongSortRule,
    TagApiApi,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from optparse import Values

    from beets import library
    from beets.autotag.hooks import AlbumInfo, TrackInfo
    from beets.dbcore import Results
    from beets.library import Item, Library

    from .vocadb_api_client import (
        AlbumForApiContract,
        AlbumForApiContractPartialFindResult,
        SongForApiContract,
        SongForApiContractPartialFindResult,
    )

    class BaseConfig(TypedDict):
        prefer_romaji: bool
        include_featured_album_artists: bool
        use_base_voicebank: bool
        search_limit: int
        exclude_item_fields: list[str]
        exclude_album_fields: list[str]


USER_AGENT: str = f"beets/{beets_version} +https://beets.io/"

DEFAULT_CONFIG: BaseConfig = {
    "prefer_romaji": False,
    "include_featured_album_artists": False,
    "use_base_voicebank": False,
    "search_limit": 5,
    "exclude_item_fields": [],
    "exclude_album_fields": [],
}

LANGUAGES: list[str] | None = beets_config["import"]["languages"].as_str_seq()
VA_NAME: str = beets_config["va_name"].as_str()
IGNORE_VIDEO_TRACKS: bool = beets_config["match"]["ignore_video_tracks"].get(
    template=bool
)

SONG_FIELDS: SongOptionalFieldsSet = SongOptionalFieldsSet(
    (
        SongOptionalFields.ARTISTS,
        SongOptionalFields.CULTURE_CODES,
        SongOptionalFields.TAGS,
        SongOptionalFields.BPM,
        SongOptionalFields.LYRICS,
    )
)


class PluginBase(MetadataSourcePlugin):
    """Base plugin class for integration of VocaDB instances with Beets.

    This base class provides the core functionality for retrieving metadata from
    an instance of VocaDB and saving it to a Beets library. Examples of VocaDB
    instances include VocaDB, UtaiteDB and TouhouDB. Subclassing is required.
    """

    _flexible_attributes: FlexibleAttributes

    base_url: httpx.URL | str
    api_url: httpx.URL | str
    sync_subcommand: str

    def __init__(self) -> None:
        super().__init__()  # pyright: ignore[reportUnknownMemberType]
        self._flexible_attributes = FlexibleAttributes(
            prefix=self.name,
        )
        self.album_types: dict[
            str, dbcore.types.String | dbcore.types.DelimitedString
        ] = {
            self._flexible_attributes.album[
                AlbumFlexibleAttributes.ALBUM_ID
            ]: dbcore.types.STRING,
            self._flexible_attributes.album[
                AlbumFlexibleAttributes.ALBUMARTIST_ID
            ]: dbcore.types.STRING,
            self._flexible_attributes.album[
                AlbumFlexibleAttributes.ALBUMARTIST_IDS
            ]: dbcore.types.MULTI_VALUE_DSV,
        }
        self.item_types: dict[
            str, dbcore.types.String | dbcore.types.DelimitedString
        ] = {
            self._flexible_attributes.item[
                ItemFlexibleAttributes.TRACK_ID
            ]: dbcore.types.STRING,
            self._flexible_attributes.item[
                ItemFlexibleAttributes.ARTIST_ID
            ]: dbcore.types.STRING,
            self._flexible_attributes.item[
                ItemFlexibleAttributes.ARTIST_IDS
            ]: dbcore.types.MULTI_VALUE_DSV,
            self._flexible_attributes.item[
                ItemFlexibleAttributes.ARRANGER_IDS
            ]: dbcore.types.MULTI_VALUE_DSV,
            self._flexible_attributes.item[
                ItemFlexibleAttributes.COMPOSER_IDS
            ]: dbcore.types.MULTI_VALUE_DSV,
            self._flexible_attributes.item[
                ItemFlexibleAttributes.LYRICIST_IDS
            ]: dbcore.types.MULTI_VALUE_DSV,
            self._flexible_attributes.item[
                ItemFlexibleAttributes.REMIXER_IDS
            ]: dbcore.types.MULTI_VALUE_DSV,
        }
        self.config.add(value=DEFAULT_CONFIG)
        self.prefer_romaji: bool = self.config["prefer_romaji"].get(bool)
        self.include_featured_album_artists: bool = self.config[
            "include_featured_album_artists"
        ].get(bool)
        self.use_base_voicebank: bool = self.config["use_base_voicebank"].get(
            bool
        )
        self.search_limit: int = self.config["search_limit"].get(int)
        self.exclude_album_fields: list[str] = self.config[
            "exclude_album_fields"
        ].as_str_seq()
        self.exclude_item_fields: list[str] = self.config[
            "exclude_item_fields"
        ].as_str_seq()

    def __init_subclass__(
        cls,
        base_url: httpx.URL | str,
        api_url: httpx.URL | str,
        subcommand_prefix: str,
    ) -> None:
        super().__init_subclass__()
        cls.base_url = base_url
        cls.api_url = api_url
        cls.sync_subcommand = f"{subcommand_prefix}sync"

    @cached_property
    def client(self) -> ApiClient:
        return ApiClient(
            user_agent=USER_AGENT, base_url=self.api_url, logger=self._log
        )

    @cached_property
    def album_api(self) -> AlbumApiApi:
        return AlbumApiApi(api_client=self.client)

    @cached_property
    def artist_api(self) -> ArtistApiApi:
        return ArtistApiApi(api_client=self.client)

    @cached_property
    def song_api(self) -> SongApiApi:
        return SongApiApi(api_client=self.client)

    @cached_property
    def tag_api(self) -> TagApiApi:
        return TagApiApi(api_client=self.client)

    @cached_property
    def language_preference(self) -> ContentLanguagePreference:
        return get_language_preference(
            languages=LANGUAGES,
            prefer_romaji=self.prefer_romaji,
        )

    @cached_property
    def mapper(self) -> Mapper:
        return Mapper(
            base_url=self.base_url,
            data_source=self.data_source,
            flexible_attributes=self._flexible_attributes,
            ignore_video_tracks=IGNORE_VIDEO_TRACKS,
            artist_api=self.artist_api,
            song_api=self.song_api,
            tag_api=self.tag_api,
            language_preference=self.language_preference,
            include_featured_album_artists=self.include_featured_album_artists,
            use_base_voicebank=self.use_base_voicebank,
            exclude_item_fields=self.exclude_item_fields,
            exclude_album_fields=self.exclude_album_fields,
            va_name=VA_NAME,
            logger=self._log,
        )

    @override
    def commands(self) -> Sequence[Subcommand]:
        sync_cmd: Subcommand = Subcommand(
            name=self.sync_subcommand,
            help=f"update metadata from {self.data_source}",
        )
        _ = sync_cmd.parser.add_option(  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
            "-p",
            "--pretend",
            action="store_true",
            help="show all changes but do nothing",
        )
        _ = sync_cmd.parser.add_option(  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
            "-m",
            "--move",
            action="store_true",
            dest="move",
            help="move files in the library directory",
        )
        _ = sync_cmd.parser.add_option(  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
            "-M",
            "--nomove",
            action="store_false",
            dest="move",
            help="don't move files in library",
        )
        _ = sync_cmd.parser.add_option(  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
            "-W",
            "--nowrite",
            action="store_false",
            default=None,
            dest="write",
            help="don't write updated metadata to files",
        )
        _ = sync_cmd.parser.add_format_option()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        sync_cmd.func = self.sync
        return [sync_cmd]

    def sync(self, lib: Library, opts: Values, args: list[str]) -> None:
        """Command handler for the VocaDB sync subcommand.

        Handles the execution of the sync command for both singleton tracks
        and albums, applying metadata updates from VocaDB to the Beets library.

        Args:
            lib: Beets library instance
            opts: Command line options parsed from argparse
            args: Command line arguments (typically query strings)
        """
        move: bool = should_move(move_opt=opts.move)  # pyright: ignore[reportAny]
        pretend: bool = opts.pretend  # pyright: ignore[reportAny]
        write: bool = should_write(write_opt=opts.write)  # pyright: ignore[reportAny]

        self.singletons(
            lib=lib, query=args, move=move, pretend=pretend, write=write
        )
        self.albums(
            lib=lib, query=args, move=move, pretend=pretend, write=write
        )

    def singletons(
        self,
        lib: Library,
        query: list[str],
        move: bool,
        pretend: bool,
        write: bool,
    ) -> None:
        """Update metadata for singleton tracks (not part of albums).

        Args:
            lib: Beets library instance
            query: Query to filter items
            move: Whether to move files
            pretend: Show changes without applying them
            write: Whether to write changes to files
        """
        from beets.autotag import TrackMatch

        item: library.Item
        for item in lib.items(query=query + ["singleton:true"]):  # pyright: ignore[reportUnknownMemberType]
            track_id: str
            if not (
                track_id := item.get(  # pyright: ignore[reportAssignmentType,reportUnknownMemberType,reportUnknownVariableType] # pyrefly: ignore[bad-assignment]
                    key=self._flexible_attributes.item[
                        ItemFlexibleAttributes.TRACK_ID
                    ]
                )
            ):
                self._log.debug(
                    "Skipping singleton with no "
                    + self._flexible_attributes.item[
                        ItemFlexibleAttributes.TRACK_ID
                    ]
                    + ": {}",
                    item,
                )
                continue
            if not item.get(key="data_source") == self.data_source:  # pyright: ignore[reportUnknownMemberType]
                self._log.debug(
                    f"Skipping non-{self.data_source} singleton: {{}}", item
                )
                continue
            self._log.debug("Searching for track {0}", item)
            track_info: TrackInfo | None = self.track_for_id(track_id)
            if not track_info:
                self._log.info(
                    f"Recording ID not found: {track_id} " + "for track {}",
                    item,
                )
                continue
            with lib.transaction():
                TrackMatch(
                    distance=Distance(), info=track_info, item=item
                ).apply_metadata()
                if show_model_changes(new=item):
                    apply_item_changes(lib, item, move, pretend, write)

    def albums(
        self,
        lib: Library,
        query: list[str],
        move: bool,
        pretend: bool,
        write: bool,
    ) -> None:
        """Update metadata for albums and their tracks.

        Args:
            lib: Beets library instance
            query: Query to filter albums
            move: Whether to move files
            pretend: Show changes without applying them
            write: Whether to write changes to files
        """
        from contextlib import suppress

        from beets.autotag import AlbumMatch
        from beets.autotag.distance import track_distance
        from beets.util import ancestry

        album: library.Album
        for album in lib.albums(query):  # pyright: ignore[reportUnknownMemberType]
            album_id: str | int | None = album.get(  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                key=self._flexible_attributes.album[
                    AlbumFlexibleAttributes.ALBUM_ID
                ]
            )
            if not album_id:
                self._log.debug(
                    "Skipping album with no "
                    + self._flexible_attributes.album[
                        AlbumFlexibleAttributes.ALBUM_ID
                    ]
                    + ": {}",
                    album,
                )
                continue
            if not album.get(key="data_source") == self.data_source:  # pyright: ignore[reportUnknownMemberType]
                self._log.debug(
                    f"Skipping non-{self.data_source} album: {{}}", album
                )
                continue
            album_info: AlbumInfo | None = self.album_for_id(album_id=album_id)  # pyright: ignore[reportUnknownArgumentType]
            if not album_info:
                self._log.info(
                    f"Release ID {album_id} not found for album {{}}", album
                )
                continue
            items: Results[library.Item] = album.items()

            track_id: int | str | None
            track_index: dict[str, TrackInfo] = {
                str(track_id): track_info
                for track_info in album_info.tracks
                if (
                    track_id := track_info.get(
                        self._flexible_attributes.item[
                            ItemFlexibleAttributes.TRACK_ID
                        ]
                    )
                )
            }
            mapping: dict[Item, TrackInfo] = {}
            item: library.Item
            for item in items:
                # First, try to get track ID from flexible attributes
                track_id = item.get(  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                    key=self._flexible_attributes.item[
                        ItemFlexibleAttributes.TRACK_ID
                    ]
                )

                if track_id:
                    with suppress(KeyError):
                        mapping[item] = track_index[str(track_id)]  # pyright: ignore[reportUnknownArgumentType]

                        continue

                # use automatic matching
                self._log.warning(
                    f"Trying to automatch missing track ID {track_id}"
                    + " in album info for {}...",
                    album,
                )
                # Unset track id so that it won't affect distance
                item[
                    self._flexible_attributes.item[
                        ItemFlexibleAttributes.TRACK_ID
                    ]
                ] = None
                matches: dict[str, Distance] = {
                    track_id: track_distance(item, track_info)
                    for track_id, track_info in track_index.items()
                }
                new_track_id: str = min(matches, key=matches.__getitem__)
                item[
                    self._flexible_attributes.item[
                        ItemFlexibleAttributes.TRACK_ID
                    ]
                ] = new_track_id
                mapping[item] = track_index[new_track_id]
                self._log.warning(
                    msg=f"Success, automatched to ID {new_track_id}"
                )

            self._log.debug("applying changes to {}", album)
            with lib.transaction():
                AlbumMatch(
                    distance=Distance(), info=album_info, mapping=mapping
                ).apply_metadata()
                changed: bool = False
                any_changed_item: library.Item | None = items.get()
                for item in items:
                    item_changed: bool = show_model_changes(new=item)
                    changed |= item_changed
                    if item_changed:
                        any_changed_item = item
                        apply_item_changes(lib, item, move, pretend, write)
                if pretend or not changed or not any_changed_item:
                    continue
                key: str
                for key in set(album.item_keys) - {
                    "original_day",
                    "original_month",
                    "original_year",
                    "genres",
                    "language",
                    "script",
                }:
                    album[key] = any_changed_item[key]
                # Copy flexible attributes from album_info to album
                for flex_key in self._flexible_attributes.album.values():
                    if flex_key in album_info:
                        album[flex_key] = album_info[flex_key]
                album.store()  # pyright: ignore[reportUnknownMemberType]
                if move and lib.directory in ancestry(
                    path=any_changed_item.path
                ):
                    self._log.debug("moving album {}", album)
                    album.move()  # pyright: ignore[reportUnknownMemberType]

    @override
    def candidates(
        self,
        items: Iterable[library.Item],
        artist: str,
        album: str,
        va_likely: bool,
    ) -> Iterable[AlbumInfo]:
        self._log.debug(msg=f"Searching for album {album}")
        remote_album_find_result: (
            AlbumForApiContractPartialFindResult | None
        ) = self.album_api.api_albums_get(
            query=album,
            maxResults=self.search_limit,
            nameMatchMode=NameMatchMode.AUTO,
        )
        remote_album_candidates: tuple[AlbumForApiContract, ...] | None
        if not remote_album_find_result or not (
            remote_album_candidates := remote_album_find_result.items
        ):
            return
        else:
            self._log.debug(
                msg=f"Found {len(remote_album_candidates)} result(s) for '{album}'"
            )
        # songFields parameter doesn't exist for album search
        # so we'll get albums by their id
        yield from filter(
            None,
            (
                self.album_for_id(album_id=remote_album_candidate.id)
                for remote_album_candidate in remote_album_candidates
            ),
        )

    @override
    def item_candidates(
        self, item: library.Item, artist: str, title: str
    ) -> Iterable[TrackInfo]:
        self._log.debug(msg=f"Searching for track {title}")
        remote_item_find_result: SongForApiContractPartialFindResult | None = (
            self.song_api.api_songs_get(
                query=title,
                fields=SONG_FIELDS,
                maxResults=self.search_limit,
                nameMatchMode=NameMatchMode.AUTO,
                preferAccurateMatches=True,
                sort=SongSortRule.SONG_TYPE,
                lang=self.language_preference,
            )
        )
        remote_item_candidates: tuple[SongForApiContract, ...] | None
        if not remote_item_find_result or not (
            remote_item_candidates := remote_item_find_result.items
        ):
            self._log.debug(msg=f"Found 0 results for '{title}'")
            return
        self._log.debug(
            msg=f"Found {len(remote_item_candidates)} result(s) for '{title}'"
        )
        yield from filter(
            None,
            map(
                self.mapper.track_info,
                remote_item_candidates,
            ),
        )

    @override
    def album_for_id(self, album_id: int | str) -> AlbumInfo | None:
        if isinstance(album_id, str) and not album_id.isnumeric():
            self._log.debug(
                msg=f"Skipping non-{self.data_source} album: {album_id}"
            )
            return None
        self._log.debug(msg=f"Searching for album {album_id}")
        remote_album: AlbumForApiContract | None = (
            self.album_api.api_albums_id_get(
                id=int(album_id),
                fields=AlbumOptionalFieldsSet(
                    (
                        AlbumOptionalFields.ARTISTS,
                        AlbumOptionalFields.DISCS,
                        AlbumOptionalFields.TAGS,
                        AlbumOptionalFields.TRACKS,
                        AlbumOptionalFields.WEB_LINKS,
                        AlbumOptionalFields.MAIN_PICTURE,
                    )
                ),
                songFields=SONG_FIELDS,
                lang=self.language_preference,
            )
        )
        return (
            self.mapper.album_info(
                remote_album=remote_album,
            )
            if remote_album
            else None
        )

    @override
    def track_for_id(self, track_id: int | str) -> TrackInfo | None:
        if isinstance(track_id, str) and not track_id.isnumeric():
            self._log.debug(
                msg=f"Skipping non-{self.data_source} singleton: {track_id}"
            )
            return None
        self._log.debug(msg=f"Searching for track {track_id}")
        remote_song: SongForApiContract | None = self.song_api.api_songs_id_get(
            id=int(track_id),
            fields=SONG_FIELDS,
            lang=self.language_preference,
        )
        return (
            self.mapper.track_info(
                remote_song=remote_song,
            )
            if remote_song
            else None
        )
