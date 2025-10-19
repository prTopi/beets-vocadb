from __future__ import annotations

import sys

from beetsplug.vocadb.lyrics_processor import LyricsProcessor
from beetsplug.vocadb.mapper import (
    AlbumFlexibleAttributes,
    FlexibleAttributes,
    ItemFlexibleAttributes,
    Mapper,
)
from beetsplug.vocadb.utils import get_id

if not sys.version_info < (3, 12):
    from typing import override  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import override

from typing import TYPE_CHECKING

import httpx
from beets import __version__ as beets_version
from beets import config as beets_config
from beets import dbcore
from beets.metadata_plugins import MetadataSourcePlugin
from beets.plugins import apply_item_changes
from beets.ui import (
    Subcommand,
    should_move,  # pyright: ignore[reportUnknownVariableType]
    should_write,  # pyright: ignore[reportUnknownVariableType]
    show_model_changes,  # pyright: ignore[reportUnknownVariableType]
)

from beetsplug.vocadb.plugin_config import InstanceConfig
from beetsplug.vocadb.vocadb_api_client import (
    AlbumApiApi,
    AlbumOptionalFields,
    AlbumOptionalFieldsSet,
    ApiClient,
    NameMatchMode,
    SongApiApi,
    SongOptionalFields,
    SongOptionalFieldsSet,
    SongSortRule,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from optparse import Values

    from beets import library
    from beets.autotag.distance import Distance
    from beets.autotag.hooks import AlbumInfo, TrackInfo
    from beets.dbcore import Results
    from beets.library import Library

    from beetsplug.vocadb.vocadb_api_client import (
        AlbumForApiContract,
        AlbumForApiContractPartialFindResult,
        SongForApiContract,
        SongForApiContractPartialFindResult,
    )

USER_AGENT: str = f"beets/{beets_version} +https://beets.io/"

SONG_FIELDS: SongOptionalFieldsSet = SongOptionalFieldsSet(
    (
        SongOptionalFields.ARTISTS,
        SongOptionalFields.CULTURE_CODES,
        SongOptionalFields.TAGS,
        SongOptionalFields.BPM,
        SongOptionalFields.LYRICS,
    )
)


class PluginBases:
    """Wrapper to prevent PluginBase from being initialized directly"""

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
            client: ApiClient = ApiClient(
                user_agent=USER_AGENT, base_url=self.api_url, logger=self._log
            )
            self.album_api: AlbumApiApi = AlbumApiApi(api_client=client)
            self.song_api: SongApiApi = SongApiApi(api_client=client)
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
            }
            self.instance_config: InstanceConfig = (
                InstanceConfig.from_config_view(config=self.config)
            )
            self.config.add(value=(self.instance_config).to_dict())  # pyright: ignore[reportUnknownMemberType]
            self.lyrics_processor: LyricsProcessor = LyricsProcessor(
                language_preference=self.instance_config.language
            )
            self.mapper: Mapper = Mapper(
                base_url=self.base_url,
                data_source=self.data_source,  # pyright: ignore[reportAny]
                flexible_attributes=self._flexible_attributes,
                ignore_video_tracks=beets_config["match"][  # pyright: ignore[reportArgumentType]
                    "ignore_video_tracks"
                ].get(template=bool),
                include_featured_album_artists=self.instance_config.include_featured_album_artists,
                language_preference=self.instance_config.language,
            )

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

        @override
        def commands(self) -> Sequence[Subcommand]:
            sync_cmd: Subcommand = Subcommand(
                name=self.sync_subcommand,
                help=f"update metadata from {self.data_source}",  # pyright: ignore[reportAny]
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
            from beets.autotag import apply_item_metadata

            item: library.Item
            for item in lib.items(query=query + ["singleton:true"]):  # pyright: ignore[reportUnknownMemberType]
                item_formatted: str = format(item)
                if not (
                    track_id := get_id(
                        entity=item,
                        preferred_key=self._flexible_attributes.item[
                            ItemFlexibleAttributes.TRACK_ID
                        ],
                        fallback_key="mb_trackid",
                    )
                ):
                    self._log.debug(
                        msg="Skipping singleton with no "
                        + self._flexible_attributes.item[
                            ItemFlexibleAttributes.TRACK_ID
                        ]
                        + f" or mb_trackid: {item_formatted}"
                    )
                    continue
                if not item.get(key="data_source") == self.data_source:  # pyright: ignore[reportAny,reportUnknownMemberType]
                    self._log.debug(
                        msg=f"Skipping non-{self.data_source} singleton: "  # pyright: ignore[reportAny]
                        + item_formatted
                    )
                    continue
                self._log.debug("Searching for track {0}", item_formatted)
                track_info: TrackInfo | None = self.track_for_id(track_id)
                if not track_info:
                    self._log.info(
                        msg=f"Recording ID not found: {track_id} "
                        + f"for track {item_formatted}"
                    )
                    continue
                with lib.transaction():
                    apply_item_metadata(item, track_info)
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
            from beets.autotag import apply_metadata
            from beets.autotag.distance import track_distance
            from beets.util import ancestry

            album: library.Album
            for album in lib.albums(query):  # pyright: ignore[reportUnknownMemberType]
                album_formatted: str = format(album)
                album_id: str | None = get_id(
                    entity=album,
                    preferred_key=self._flexible_attributes.album[
                        AlbumFlexibleAttributes.ALBUM_ID
                    ],
                    fallback_key="mb_albumid",
                )
                if not album_id:
                    self._log.debug(
                        msg="Skipping album with no "
                        + self._flexible_attributes.album[
                            AlbumFlexibleAttributes.ALBUM_ID
                        ]
                        + f" or mb_albumid: {album_formatted}"
                    )
                    continue
                if not album.get(key="data_source") == self.data_source:  # pyright: ignore[reportAny,reportUnknownMemberType]
                    self._log.debug(
                        msg=f"Skipping non-{self.data_source} album: {album_formatted}"  # pyright: ignore[reportAny]
                    )
                    continue
                album_info: AlbumInfo | None = self.album_for_id(
                    album_id=album_id
                )
                if not album_info:
                    self._log.info(
                        msg=f"Release ID {album_id} "
                        + f"not found for album {album_formatted}"
                    )
                    continue
                items: Results[library.Item] = album.items()

                plugin_track_id: int | None
                track_id: str | None
                track_index: dict[str, TrackInfo] = {
                    track_id: track_info
                    for track_info in album_info.tracks
                    if (
                        track_id := get_id(
                            entity=track_info,
                            preferred_key=self._flexible_attributes.item[
                                ItemFlexibleAttributes.TRACK_ID
                            ],
                            fallback_key="track_id",
                        )
                    )
                }
                mapping: dict[library.Item, TrackInfo] = {}
                item: library.Item
                for item in items:
                    # First, try to get track ID from flexible attributes
                    plugin_track_id = item.get(  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                        key=self._flexible_attributes.item[
                            ItemFlexibleAttributes.TRACK_ID
                        ]
                    )

                    if plugin_track_id:
                        try:
                            mapping[item] = track_index[str(plugin_track_id)]  # pyright: ignore[reportUnknownArgumentType]
                            continue
                        except KeyError:
                            ...  # Fall through to try mb_trackid

                    # Fall back to mb_trackid
                    mb_trackid: str | None = item.get("mb_trackid")  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                    if mb_trackid and mb_trackid.isnumeric():  # pyright: ignore[reportUnknownMemberType]
                        try:
                            mapping[item] = track_index[mb_trackid]
                            item[
                                self._flexible_attributes.item[
                                    ItemFlexibleAttributes.TRACK_ID
                                ]
                            ] = mb_trackid
                            continue
                        except KeyError:
                            ...  # Fall through to automatic matching

                    # If neither flexible attribute nor mb_trackid work,
                    # use automatic matching
                    current_track_id: str | None = (  # pyright: ignore[reportUnknownVariableType]
                        str(plugin_track_id) or mb_trackid  # pyright: ignore[reportUnknownArgumentType]
                    )

                    self._log.warning(
                        msg="No track found for "
                        + f"{plugin_track_id=}, {mb_trackid=}, {current_track_id=}"
                    )

                    self._log.warning(
                        msg=f"Trying to automatch missing track ID {current_track_id}"
                        + f" in album info for {album_formatted}..."
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
                    new_track_id: str = min(matches, key=lambda k: matches[k])
                    item[
                        self._flexible_attributes.item[
                            ItemFlexibleAttributes.TRACK_ID
                        ]
                    ] = new_track_id
                    mapping[item] = track_index[new_track_id]
                    self._log.warning(
                        msg=f"Success, automatched to ID {new_track_id}"
                    )

                self._log.debug(msg=f"applying changes to {album_formatted}")
                with lib.transaction():
                    apply_metadata(album_info, mapping)
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
                        "genre",
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
                        self._log.debug(msg=f"moving album {album_formatted}")
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
                maxResults=self.instance_config.search_limit,
                nameMatchMode=NameMatchMode.AUTO,
            )
            remote_album_candidates: tuple[AlbumForApiContract, ...] | None
            if not remote_album_find_result or not (
                remote_album_candidates := remote_album_find_result.items
            ):
                return
            self._log.debug(
                msg=f"Found {len(remote_album_candidates)} result(s) for '{album}'"
            )
            # songFields parameter doesn't exist for album search
            # so we'll get albums by their id
            yield from filter(
                None,
                map(
                    lambda remote_album_candidate: self.album_for_id(
                        album_id=str(remote_album_candidate.id)
                    ),
                    remote_album_candidates,
                ),
            )

        @override
        def item_candidates(
            self, item: library.Item, artist: str, title: str
        ) -> Iterable[TrackInfo]:
            self._log.debug(msg=f"Searching for track {title}")
            remote_item_find_result: (
                SongForApiContractPartialFindResult | None
            ) = self.song_api.api_songs_get(
                query=title,
                fields=SONG_FIELDS,
                maxResults=self.instance_config.search_limit,
                nameMatchMode=NameMatchMode.AUTO,
                preferAccurateMatches=True,
                sort=SongSortRule.SONG_TYPE,
                lang=self.instance_config.language,
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
                None, map(self.mapper.track_info, remote_item_candidates)
            )

        @override
        def album_for_id(self, album_id: str) -> AlbumInfo | None:
            if not album_id.isnumeric():
                self._log.debug(
                    msg=f"Skipping non-{self.data_source} album: {album_id}"  # pyright: ignore[reportAny]
                )
                return
            self._log.debug(msg=f"Searching for album {album_id}")
            remote_album: AlbumForApiContract | None = (
                self.album_api.api_albums_id_get(
                    id=int(album_id),
                    fields=AlbumOptionalFieldsSet(
                        {
                            AlbumOptionalFields.ARTISTS,
                            AlbumOptionalFields.DISCS,
                            AlbumOptionalFields.TAGS,
                            AlbumOptionalFields.TRACKS,
                            AlbumOptionalFields.WEB_LINKS,
                        }
                    ),
                    songFields=SONG_FIELDS,
                    lang=self.instance_config.language,
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
        def track_for_id(self, track_id: str) -> TrackInfo | None:
            if not track_id.isnumeric():
                self._log.debug(
                    msg=f"Skipping non-{self.data_source} singleton: {track_id}"  # pyright: ignore[reportAny]
                )
                return
            self._log.debug(msg=f"Searching for track {track_id}")
            remote_song: SongForApiContract | None = (
                self.song_api.api_songs_id_get(
                    id=int(track_id),
                    fields=SONG_FIELDS,
                    lang=self.instance_config.language,
                )
            )
            return (
                self.mapper.track_info(
                    remote_song=remote_song,
                )
                if remote_song
                else None
            )
