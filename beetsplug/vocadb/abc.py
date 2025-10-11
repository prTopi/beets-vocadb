from __future__ import annotations

import abc
import sys

if not sys.version_info < (3, 12):
    from typing import override  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import override

from re import match, search
from typing import TYPE_CHECKING

import httpx
from beets import __version__ as beets_version
from beets import autotag, dbcore, ui, util
from beets import config as beets_config
from beets.autotag.distance import track_distance
from beets.autotag.hooks import AlbumInfo, TrackInfo
from beets.metadata_plugins import MetadataSourcePlugin
from beets.plugins import apply_item_changes
from beets.ui import (
    Subcommand,
    show_model_changes,  # pyright: ignore[reportUnknownVariableType]
)

from beetsplug.vocadb.plugin_config import VA_NAME, InstanceConfig
from beetsplug.vocadb.vocadb_api_client import (
    AlbumApiApi,
    AlbumDiscPropertiesContract,
    AlbumOptionalFields,
    AlbumOptionalFieldsSet,
    ApiClient,
    ArtistCategories,
    ArtistRoles,
    ContentLanguagePreference,
    DiscMediaType,
    DiscType,
    NameMatchMode,
    SongApiApi,
    SongOptionalFields,
    SongOptionalFieldsSet,
    SongSortRule,
    TagBaseContract,
    TranslationType,
)
from beetsplug.vocadb.vocadb_api_client.models import StrEnum

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from datetime import datetime
    from optparse import Values
    from re import Match

    from beets import library
    from beets.autotag.distance import Distance
    from beets.library import Library
    from typing_extensions import TypeAlias

    from beetsplug.vocadb.vocadb_api_client import (
        AlbumForApiContract,
        AlbumForApiContractPartialFindResult,
        ArtistForAlbumForApiContract,
        ArtistForSongContract,
        LyricsForSongContract,
        OptionalDateTimeContract,
        SongForApiContract,
        SongForApiContractPartialFindResult,
        SongInAlbumForApiContract,
        TagUsageForApiContract,
        WebLinkForApiContract,
    )


SongOrAlbumArtists: TypeAlias = (
    "list[ArtistForAlbumForApiContract] | list[ArtistForSongContract]"
)

USER_AGENT: str = f"beets/{beets_version} +https://beets.io/"

SONG_FIELDS: SongOptionalFieldsSet = SongOptionalFieldsSet(
    {
        SongOptionalFields.ARTISTS,
        SongOptionalFields.CULTURECODES,
        SongOptionalFields.TAGS,
        SongOptionalFields.BPM,
        SongOptionalFields.LYRICS,
    }
)


class AlbumFlexibleAttributes(StrEnum):
    ALBUM_ID = "album_id"
    ARTIST_ID = "albumartist_id"
    ARTIST_IDS = "albumartist_ids"


class ItemFlexibleAttributes(StrEnum):
    TRACK_ID = "track_id"
    ARTIST_ID = "artist_id"
    ARTIST_IDS = "artist_ids"


# TODO: this sucks
class FlexibleAttributes:
    def __init__(self, prefix: str) -> None:
        """Add prefix to all attributes in each field.

        Args:
            prefix: String prefix to add to attribute names

        Returns:
            New FlexibleAttributes instance with prefixed attributes
        """

        self.album: dict[AlbumFlexibleAttributes, str] = {
            arg: f"{prefix}_{arg}" for arg in AlbumFlexibleAttributes
        }
        self.item: dict[ItemFlexibleAttributes, str] = {
            arg: f"{prefix}_{arg}" for arg in ItemFlexibleAttributes
        }


class ProcessedArtistCategories(StrEnum):
    PRODUCERS = "producers"
    COMPOSERS = "composers"
    ARRANGERS = "arrangers"
    LYRICISTS = "lyricists"
    CIRCLES = "circles"
    VOCALISTS = "vocalists"


class CategorizedArtists(
    dict[
        ProcessedArtistCategories,
        dict[str, str],
    ]
):
    def __init__(self) -> None:
        super().__init__()
        # Initialize all expected keys
        for key in ProcessedArtistCategories:
            self[key] = {}


class PluginABCs:
    class PluginABC(MetadataSourcePlugin, metaclass=abc.ABCMeta):
        _flexible_attributes: FlexibleAttributes
        _default_config: InstanceConfig | None = None

        base_url: httpx.URL | str
        api_url: httpx.URL | str
        subcommand: str

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
                    AlbumFlexibleAttributes.ARTIST_ID
                ]: dbcore.types.STRING,
                self._flexible_attributes.album[
                    AlbumFlexibleAttributes.ARTIST_IDS
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
                InstanceConfig.from_config_view(
                    config=self.config, default=self._default_config
                )
            )
            self.config.add(value=(self.instance_config).to_dict())  # pyright: ignore[reportUnknownMemberType]

        def __init_subclass__(
            cls,
            base_url: httpx.URL | str,
            api_url: httpx.URL | str,
            subcommand: str,
        ) -> None:
            super().__init_subclass__()
            cls._default_config = InstanceConfig.from_config_view(
                config=beets_config["vocadb"]
            )
            cls.base_url = base_url
            cls.api_url = api_url
            cls.subcommand = subcommand

        @override
        def commands(self) -> Sequence[Subcommand]:
            cmd: Subcommand = Subcommand(
                name=self.subcommand,
                help=f"update metadata from {self.data_source}",  # pyright: ignore[reportAny]
            )
            _ = cmd.parser.add_option(  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                "-p",
                "--pretend",
                action="store_true",
                help="show all changes but do nothing",
            )
            _ = cmd.parser.add_option(  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                "-m",
                "--move",
                action="store_true",
                dest="move",
                help="move files in the library directory",
            )
            _ = cmd.parser.add_option(  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                "-M",
                "--nomove",
                action="store_false",
                dest="move",
                help="don't move files in library",
            )
            _ = cmd.parser.add_option(  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                "-W",
                "--nowrite",
                action="store_false",
                default=None,
                dest="write",
                help="don't write updated metadata to files",
            )
            _ = cmd.parser.add_format_option()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
            cmd.func = self.func
            return [cmd]

        def func(self, lib: Library, opts: Values, args: list[str]) -> None:
            """Command handler for the *dbsync function."""
            move: bool = ui.should_move(move_opt=opts.move)  # pyright: ignore[reportAny,reportUnknownMemberType]
            pretend: bool = opts.pretend  # pyright: ignore[reportAny]
            write: bool = ui.should_write(write_opt=opts.write)  # pyright: ignore[reportAny,reportUnknownMemberType]
            query: list[str] = ui.decargs(arglist=args)  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]

            self.singletons(lib, query, move, pretend, write)  # pyright: ignore[reportUnknownArgumentType]
            self.albums(lib, query, move, pretend, write)  # pyright: ignore[reportUnknownArgumentType]

        def singletons(
            self,
            lib: Library,
            query: list[str],
            move: bool,
            pretend: bool,
            write: bool,
        ) -> None:
            item: library.Item
            for item in lib.items(query=query + ["singleton:true"]):  # pyright: ignore[reportUnknownMemberType]
                item_formatted: str = format(item)
                track_id: str | None = None
                plugin_track_id: int | None = item.get(  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                    key=self._flexible_attributes.item[
                        ItemFlexibleAttributes.TRACK_ID
                    ]
                )
                if plugin_track_id:
                    track_id = str(plugin_track_id)  # pyright: ignore[reportUnknownArgumentType]
                else:
                    mb_trackid: str | None = item.get(key="mb_trackid")  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                    if mb_trackid:
                        track_id = mb_trackid  # pyright: ignore[reportUnknownVariableType]
                if not track_id:
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
                track_info: TrackInfo | None = self.track_for_id(track_id)  # pyright: ignore[reportUnknownArgumentType]
                if not track_info:
                    self._log.info(
                        msg=f"Recording ID not found: {track_id} "
                        + f"for track {item_formatted}"
                    )
                    continue
                with lib.transaction():
                    autotag.apply_item_metadata(item, track_info)
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
            """Retrieve and apply info from the autotagger for albums matched by
            query and their items.
            """
            album: library.Album
            for album in lib.albums(query):  # pyright: ignore[reportUnknownMemberType]
                album_formatted: str = format(album)
                album_id: str | None = None
                plugin_album_id: int | None = album.get(  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                    key=self._flexible_attributes.album[
                        AlbumFlexibleAttributes.ALBUM_ID
                    ]
                )
                if plugin_album_id:
                    album_id = str(plugin_album_id)  # pyright: ignore[reportUnknownArgumentType]
                else:
                    mb_albumid: str | None = album.get(key="mb_albumid")  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                    if mb_albumid:
                        album_id = mb_albumid  # pyright: ignore[reportUnknownVariableType]
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
                    album_id=album_id  # pyright: ignore[reportUnknownArgumentType]
                )
                if not album_info:
                    self._log.info(
                        msg=f"Release ID {album_id} "
                        + f"not found for album {album_formatted}"
                    )
                    continue
                items: dbcore.Results[library.Item] = album.items()

                plugin_track_id: int | None
                track_id: str | None
                track_index: dict[str, TrackInfo] = {
                    track_id: track_info
                    for track_info in album_info.tracks
                    if (
                        track_id := str(plugin_track_id)
                        if (
                            plugin_track_id := track_info.get(
                                self._flexible_attributes.item[
                                    ItemFlexibleAttributes.TRACK_ID
                                ]
                            )
                        )
                        else (track_info.track_id)
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
                    autotag.apply_metadata(album_info, mapping)
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
                    if move and lib.directory in util.ancestry(
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
            remote_album_candidates: list[AlbumForApiContract] | None
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
                        str(remote_album_candidate.id)
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
                sort=SongSortRule.SONGTYPE,
                lang=self.instance_config.language,
            )
            remote_item_candidates: list[SongForApiContract] | None
            if not remote_item_find_result or not (
                remote_item_candidates := remote_item_find_result.items
            ):
                self._log.debug(msg=f"Found 0 results for '{title}'")
                return
            self._log.debug(
                msg=f"Found {len(remote_item_candidates)} result(s) for '{title}'"
            )
            yield from map(self.track_info, remote_item_candidates)

        @override
        def album_for_id(self, album_id: str) -> AlbumInfo | None:
            if not album_id.isnumeric():
                self._log.debug(
                    msg=f"Skipping non-{self.data_source} album: {album_id}"  # pyright: ignore[reportAny]
                )
                return None
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
                            AlbumOptionalFields.WEBLINKS,
                        }
                    ),
                    songFields=SONG_FIELDS,
                    lang=self.instance_config.language,
                )
            )
            return (
                self.album_info(
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
                return None
            self._log.debug(msg=f"Searching for track {track_id}")
            remote_track: SongForApiContract | None = (
                self.song_api.api_songs_id_get(
                    id=int(track_id),
                    fields=SONG_FIELDS,
                    lang=self.instance_config.language,
                )
            )
            return (
                self.track_info(
                    remote_track=remote_track,
                )
                if remote_track
                else None
            )

        def album_info(
            self,
            remote_album: AlbumForApiContract,
        ) -> AlbumInfo | None:
            if not remote_album.tracks:
                return None
            # grouped_remote_tracks: defaultdict[
            #     int, list[SongInAlbumForApiContract]
            # ] = defaultdict(list[SongInAlbumForApiContract])
            # for remote_track in remote_album.tracks:
            #     grouped_remote_tracks[remote_track.disc_number].append(remote_track)
            if not remote_album.discs:
                remote_album.discs = [
                    AlbumDiscPropertiesContract(
                        disc_number=i + 1,
                        id=0,
                        name="CD",
                        media_type=DiscMediaType.AUDIO,
                    )
                    for i in range(
                        max(
                            {
                                remote_track.disc_number
                                for remote_track in remote_album.tracks
                            },
                            default=1,
                        )
                    )
                ]
            ignored_discs: set[int] = set()
            remote_disc: AlbumDiscPropertiesContract
            for remote_disc in remote_album.discs:
                disc_number: int = remote_disc.disc_number
                if (
                    remote_disc.media_type == DiscMediaType.VIDEO
                    and beets_config["match"]["ignore_video_tracks"].get(
                        template=bool
                    )
                    or not remote_album.tracks
                ):
                    ignored_discs.add(disc_number)
                    continue
                remote_disc.total = max(
                    {
                        remote_track.track_number
                        for remote_track in remote_album.tracks
                        if remote_track.disc_number == disc_number
                    }
                )

            remote_disc_type: DiscType
            va: bool = (
                remote_disc_type := remote_album.disc_type
            ) == DiscType.COMPILATION
            album: str | None = remote_album.name
            album_id: str = str(remote_album.id)
            artist: str
            artists: list[str]
            artists_ids: list[str]
            artist_id: str | None
            artist, artist_id, artists, artists_ids, _ = self.get_artists(
                remote_artists=remote_album.artists,
                include_featured_artists=self.instance_config.include_featured_album_artists,
                comp=va,
            )
            if artist == VA_NAME:
                va = True

            tracks: list[TrackInfo]
            script: str | None
            language: str | None
            tracks, script, language = self.get_album_track_infos(
                remote_tracks=remote_album.tracks,
                remote_discs=remote_album.discs,
                ignored_discs=ignored_discs,
            )
            asin: str | None = None
            remote_web_links: list[WebLinkForApiContract] | None
            if remote_web_links := remote_album.web_links:
                for remote_web_link in remote_web_links:
                    remote_web_link: WebLinkForApiContract
                    if (
                        not remote_web_link.disabled
                        and remote_web_link.url
                        and remote_web_link.description
                        and match(
                            pattern="Amazon( \\((LE|RE|JP|US)\\).*)?$",
                            string=remote_web_link.description,
                        )
                    ):
                        asin_match: Match[str] | None = search(
                            pattern="\\/dp\\/(.+?)(\\/|$)",
                            string=remote_web_link.url,
                        )
                        if asin_match:
                            asin = asin_match[1]
                            break
            albumtype: str = remote_disc_type.lower()
            albumtypes: list[str] = [albumtype]
            remote_date: OptionalDateTimeContract = remote_album.release_date
            year: int | None = remote_date.year
            month: int | None = remote_date.month
            day: int | None = remote_date.day
            label: str | None = None
            remote_albumartists: list[ArtistForAlbumForApiContract] | None
            remote_albumartist: ArtistForAlbumForApiContract
            if remote_albumartists := remote_album.artists:
                for remote_albumartist in remote_albumartists:
                    if ArtistCategories.LABEL in remote_albumartist.categories:
                        label = remote_albumartist.name
                        break
            remote_discs: list[AlbumDiscPropertiesContract] = remote_album.discs
            mediums: int = len(remote_discs)
            catalognum: str | None = remote_album.catalog_number
            genre: str | None = self.get_genres(
                remote_tags=remote_album.tags or []
            )
            media: str | None
            try:
                media = remote_discs[0].name
            except IndexError:
                media = None
            data_url: str = str(
                httpx.URL(url=self.base_url).join(url=f"Al/{album_id}")
            )
            album_info: AlbumInfo = AlbumInfo(
                tracks=tracks,
                album=album,
                # album_id=album_id,
                albumtype=albumtype,
                albumtypes=albumtypes,
                asin=asin,
                artist=artist,
                artists=artists,
                # artist_id=artist_id,
                artists_ids=artists_ids,
                catalognum=catalognum,
                data_source=self.data_source,  # pyright: ignore[reportAny]
                day=day,
                genre=genre,
                label=label,
                language=language,
                media=media,
                mediums=mediums,
                month=month,
                script=script,
                va=va,
                year=year,
                data_url=data_url,
            )
            album_info[
                self._flexible_attributes.album[
                    AlbumFlexibleAttributes.ALBUM_ID
                ]
            ] = album_id
            album_info[
                self._flexible_attributes.album[
                    AlbumFlexibleAttributes.ARTIST_ID
                ]
            ] = artist_id
            # album_info[
            #     self._flexible_attributes.album[AlbumFlexibleAttributes.ARTIST_IDS]
            # ] = artists_ids
            return album_info

        def track_info(
            self,
            remote_track: SongForApiContract,
            index: int | None = None,
            media: str | None = None,
            medium: int | None = None,
            medium_index: int | None = None,
            medium_total: int | None = None,
        ) -> TrackInfo:
            title: str | None
            assert (title := remote_track.name)
            track_id: str = str(remote_track.id)
            artist: str
            artists: list[str]
            artists_ids: list[str]
            artist_id: str | None
            artists_by_categories: CategorizedArtists
            artist, artist_id, artists, artists_ids, artists_by_categories = (
                self.get_artists(remote_artists=remote_track.artists)
            )

            arranger: str = ", ".join(
                artists_by_categories[ProcessedArtistCategories.ARRANGERS]
            )
            composer: str = ", ".join(
                artists_by_categories[ProcessedArtistCategories.COMPOSERS]
            )
            lyricist: str = ", ".join(
                artists_by_categories[ProcessedArtistCategories.LYRICISTS]
            )
            length: float = remote_track.length_seconds
            data_url: str = str(
                httpx.URL(url=self.base_url).join(url=f"S/{track_id}")
            )
            max_milli_bpm: int | None = remote_track.max_milli_bpm
            bpm: str | None = (
                str(max_milli_bpm // 1000) if max_milli_bpm else None
            )
            genre: str | None = self.get_genres(
                remote_tags=remote_track.tags or []
            )
            script: str | None
            language: str | None
            lyrics: str | None
            script, language, lyrics = self.get_lyrics(
                remote_lyrics_list=remote_track.lyrics,
            )
            original_day: int | None = None
            original_month: int | None = None
            original_year: int | None = None
            if remote_track.publish_date:
                date: datetime = remote_track.publish_date
                original_day = date.day
                original_month = date.month
                original_year = date.year
            track_info: TrackInfo = TrackInfo(
                title=title,
                # track_id=track_id,
                artist=artist,
                artists=artists,
                # artist_id=artist_id,
                # artists_ids=artists_ids,
                length=length,
                index=index,
                track_alt=str(index) if index else None,
                media=media,
                medium=medium,
                medium_index=medium_index,
                medium_total=medium_total,
                data_source=self.data_source,  # pyright: ignore[reportAny]
                data_url=data_url,
                lyricist=lyricist,
                composer=composer,
                arranger=arranger,
                bpm=bpm,
                genre=genre,
                script=script,
                language=language,
                lyrics=lyrics,
                original_day=original_day,
                original_month=original_month,
                original_year=original_year,
            )
            track_info[
                self._flexible_attributes.item[ItemFlexibleAttributes.TRACK_ID]
            ] = track_id
            track_info[
                self._flexible_attributes.item[ItemFlexibleAttributes.ARTIST_ID]
            ] = artist_id
            track_info[
                self._flexible_attributes.item[
                    ItemFlexibleAttributes.ARTIST_IDS
                ]
            ] = artists_ids
            return track_info

        def get_album_track_infos(
            self,
            remote_tracks: list[SongInAlbumForApiContract],
            remote_discs: Sequence[AlbumDiscPropertiesContract],
            ignored_discs: set[int],
        ) -> tuple[list[TrackInfo], str | None, str | None]:
            track_infos: list[TrackInfo] = []
            script: str | None = None
            language: str | None = None
            remote_track: SongInAlbumForApiContract
            for remote_track in remote_tracks:
                disc_number: int
                if not remote_track.song or (
                    (disc_number := remote_track.disc_number) in ignored_discs
                ):
                    continue
                format: str | None = remote_discs[disc_number - 1].name
                total: int | None = remote_discs[disc_number - 1].total
                track_info: TrackInfo = self.track_info(
                    remote_track=remote_track.song,
                    index=remote_track.track_number,
                    media=format,
                    medium=disc_number,
                    medium_index=remote_track.track_number,
                    medium_total=total,
                )
                if track_info.script and script != "Qaaa":  # pyright: ignore[reportAny]
                    if not script:
                        script = track_info.script  # pyright: ignore[reportAny]
                        language = track_info.language  # pyright: ignore[reportAny]
                    elif script != track_info.script:  # pyright: ignore[reportAny]
                        script = "Qaaa"
                        language = "mul"
                track_infos.append(track_info)
            if script == "Qaaa" or language == "mul":
                for track_info in track_infos:
                    track_info.script = script
                    track_info.language = language
            return track_infos, script, language

        def get_artists(
            self,
            remote_artists: SongOrAlbumArtists | None,
            include_featured_artists: bool = True,
            comp: bool = False,
        ) -> tuple[str, str | None, list[str], list[str], CategorizedArtists]:
            """
            Returns:
                Tuple containing:
                - Locally generated artist string
                - Artist ID of the first main artist
                or the first non-empty artist if available
                - List of unique artist names in order of first appearance
                - List of corresponding artist IDs in same order as artist names
                - ArtistsByCategories object with artists sorted into role categories
            """
            if not remote_artists:
                return "", None, [], [], CategorizedArtists()
            artists_by_categories: CategorizedArtists
            not_creditable_artists: set[str]

            artists_by_categories, not_creditable_artists = (
                self.categorize_artists(remote_artists)
            )

            main_artists: list[str] = [
                VA_NAME if comp else name
                for name in (
                    *artists_by_categories[
                        ProcessedArtistCategories.PRODUCERS
                    ].keys(),
                    *artists_by_categories[
                        ProcessedArtistCategories.CIRCLES
                    ].keys(),
                )
                if name not in not_creditable_artists
            ] or [
                name
                for name in artists_by_categories[
                    ProcessedArtistCategories.VOCALISTS
                ].keys()
                if name not in not_creditable_artists
            ]

            artist_string: str = (
                ", ".join(main_artists)
                if not len(main_artists) > 5
                else VA_NAME
            )

            featured_artists: list[str] = []

            if (
                include_featured_artists
                and artists_by_categories[ProcessedArtistCategories.VOCALISTS]
                and (comp or main_artists)
            ):
                featured_artists.extend(
                    name
                    for name in artists_by_categories[
                        ProcessedArtistCategories.VOCALISTS
                    ].keys()
                    if name not in not_creditable_artists
                )
                if (
                    featured_artists
                    and not len(main_artists) + len(featured_artists) > 5
                ):
                    artist_string += f" feat. {', '.join(featured_artists)}"

            artists_names: list[str]
            artists_ids: list[str]
            artists_names, artists_ids = self.extract_artists_from_categories(
                artist_by_categories=artists_by_categories
            )

            artist_id: str | None = None
            for x in *main_artists, *featured_artists:
                try:
                    if artist_id := artists_ids[artists_names.index(x)]:
                        break
                except (IndexError, ValueError):
                    ...
            if not artist_id:
                artist_id = next(filter(None, artists_ids), None)

            return (
                artist_string,
                artist_id,
                artists_names,
                artists_ids,
                artists_by_categories,
            )

        @staticmethod
        def categorize_artists(
            remote_artists: SongOrAlbumArtists,
        ) -> tuple[CategorizedArtists, set[str]]:
            """Categorizes artists by their roles and identifies not creditable artists.

            Takes a list of artists and organizes them into categories like producers,
            circles, vocalists, etc. based on their roles and categories.
            Also identifies which artists are not creditable.

            Args:
                remote_artists: List of AlbumArtist or SongArtist objects to categorize

            Returns:
                Tuple containing:
                - ArtistsByCategories object with artists sorted into role categories
                - Set of artist names that are not creditable
            """
            artists_by_categories: CategorizedArtists = CategorizedArtists()
            not_creditable_artists: set[str] = set()

            role_category_map: dict[
                ArtistCategories | ArtistRoles, ProcessedArtistCategories
            ] = {
                ArtistCategories.CIRCLE: ProcessedArtistCategories.CIRCLES,
                ArtistRoles.ARRANGER: ProcessedArtistCategories.ARRANGERS,
                ArtistRoles.COMPOSER: ProcessedArtistCategories.COMPOSERS,
                ArtistRoles.LYRICIST: ProcessedArtistCategories.LYRICISTS,
                ArtistCategories.VOCALIST: ProcessedArtistCategories.VOCALISTS,
            }

            producer_roles: set[ArtistRoles] = {
                ArtistRoles.ARRANGER,
                ArtistRoles.COMPOSER,
                ArtistRoles.LYRICIST,
            }

            remote_artist: ArtistForAlbumForApiContract | ArtistForSongContract
            for remote_artist in remote_artists:
                name: str | None
                id: str
                name, id = (
                    (remote_artist.artist.name, str(remote_artist.artist.id))
                    if remote_artist.artist
                    else (remote_artist.name, "")
                )
                assert name
                if remote_artist.is_support or any(
                    {
                        ArtistCategories.NOTHING,
                        ArtistCategories.LABEL,
                    }
                    & remote_artist.categories
                ):
                    not_creditable_artists.add(name)

                # Handle producers/bands first
                if {
                    ArtistCategories.PRODUCER,
                    # ArtistCategories.CIRCLE,
                    ArtistCategories.BAND,
                } & remote_artist.categories:
                    if "Default" in remote_artist.effective_roles:
                        remote_artist.effective_roles |= producer_roles
                    artists_by_categories[ProcessedArtistCategories.PRODUCERS][
                        name
                    ] = id

                # Apply role/category mappings
                remote_role: ArtistCategories | ArtistRoles
                category: ProcessedArtistCategories
                for remote_role, category in role_category_map.items():
                    if (
                        isinstance(remote_role, ArtistCategories)
                        and remote_role in remote_artist.categories
                    ) or remote_role in remote_artist.effective_roles:
                        artists_by_categories[category][name] = id

            # Set producer fallbacks if needed
            if (
                artists_by_categories[ProcessedArtistCategories.VOCALISTS]
                and not artists_by_categories[
                    ProcessedArtistCategories.PRODUCERS
                ]
            ):
                artists_by_categories[ProcessedArtistCategories.PRODUCERS] = (
                    artists_by_categories[ProcessedArtistCategories.VOCALISTS]
                )

            # Set other role fallbacks
            for category in (
                ProcessedArtistCategories.ARRANGERS,
                ProcessedArtistCategories.COMPOSERS,
                ProcessedArtistCategories.LYRICISTS,
            ):
                if not any(artists_by_categories[category]):
                    artists_by_categories[category] = artists_by_categories[
                        ProcessedArtistCategories.PRODUCERS
                    ]

            return artists_by_categories, not_creditable_artists

        def extract_artists_from_categories(
            self, artist_by_categories: CategorizedArtists
        ) -> tuple[list[str], list[str]]:
            """
            Extracts relevant artists and their IDs.

            Args:
                artist_by_categories:
                    ArtistsByCategories object containing categorized artists

            Returns:
                Tuple containing:
                - List of artist names in order of first appearance
                - List of corresponding artist IDs in same order as artist names
            """

            category: dict[str, str]
            artists: dict[str, str] = {}

            for category in artist_by_categories.values():
                # Merge each category's artists into the dict while preserving order
                # and preventing duplicates
                artists |= category

            # Convert dict to separate lists of artists and IDs
            artists_names: list[str] = list(artists.keys())
            artists_ids: list[str] = list(artists.values())

            return artists_names, artists_ids

        @staticmethod
        def get_genres(remote_tags: list[TagUsageForApiContract]) -> str | None:
            genres: list[str] = []
            remote_tag_usage: TagUsageForApiContract
            for remote_tag_usage in sorted(
                remote_tags, key=lambda x: x.count, reverse=True
            ):  # type: ignore[misc]
                remote_tag: TagBaseContract = remote_tag_usage.tag
                if remote_tag.category_name == "Genres" and remote_tag.name:
                    genres.append(remote_tag.name.title())
            return "; ".join(genres) if genres else None

        def get_lyrics(
            self,
            remote_lyrics_list: list[LyricsForSongContract] | None,
            translated_lyrics: bool = False,
        ) -> tuple[str | None, str | None, str | None]:
            script: str | None = None
            language: str | None = None
            lyrics: str | None = None

            remote_lyrics: LyricsForSongContract
            if remote_lyrics_list:
                language_preference: ContentLanguagePreference = (
                    self.instance_config.language
                )
                for remote_lyrics in remote_lyrics_list:
                    remote_translation_type: TranslationType = (
                        remote_lyrics.translation_type
                    )
                    value: str | None = remote_lyrics.value
                    # get the intersection
                    culture_codes: set[str] | None = remote_lyrics.culture_codes
                    if culture_codes:
                        culture_codes &= {
                            "en",
                            "ja",
                        }

                    if not culture_codes:
                        if (
                            not translated_lyrics
                            and language_preference
                            == ContentLanguagePreference.ROMAJI
                            and remote_translation_type
                            == TranslationType.ROMANIZED
                        ):
                            lyrics = value
                        continue

                    if "en" in culture_codes:
                        if remote_translation_type == TranslationType.ORIGINAL:
                            script = "Latn"
                            language = "eng"
                        if (
                            translated_lyrics
                            or language_preference
                            == ContentLanguagePreference.ENGLISH
                        ):
                            lyrics = value
                        continue

                    if "ja" in culture_codes:
                        if remote_translation_type == TranslationType.ORIGINAL:
                            script = "Jpan"
                            language = "jpn"
                        if (
                            not translated_lyrics
                            and language_preference
                            == ContentLanguagePreference.JAPANESE
                        ):
                            lyrics = value

                if not lyrics and remote_lyrics_list:
                    lyrics = self.get_fallback_lyrics(remote_lyrics_list)

            return script, language, lyrics

        def get_fallback_lyrics(
            self,
            remote_lyrics_list: list[LyricsForSongContract],
        ) -> str | None:
            language_preference: ContentLanguagePreference = (
                self.instance_config.language
            )
            remote_lyrics: LyricsForSongContract
            if language_preference == ContentLanguagePreference.ENGLISH:
                for remote_lyrics in remote_lyrics_list:
                    culture_codes: set[str] | None
                    if (
                        culture_codes := remote_lyrics.culture_codes
                    ) and "en" in culture_codes:
                        return remote_lyrics.value
                language_preference = ContentLanguagePreference.ROMAJI
            if language_preference == ContentLanguagePreference.ROMAJI:
                for remote_lyrics in remote_lyrics_list:
                    if (
                        remote_lyrics.translation_type
                        == TranslationType.ROMANIZED
                    ):
                        return remote_lyrics.value
            if language_preference == ContentLanguagePreference.DEFAULT:
                for remote_lyrics in remote_lyrics_list:
                    if (
                        remote_lyrics.translation_type
                        == TranslationType.ORIGINAL
                    ):
                        return remote_lyrics.value
            return remote_lyrics_list[0].value if remote_lyrics_list else None
