from __future__ import annotations

from contextlib import suppress
from enum import auto
from functools import cache, lru_cache
from logging import Logger
from typing import TYPE_CHECKING, TypedDict, cast

from beets.metadata_plugins import MetadataSourcePlugin
from beets.util import unique_list

from .vocadb_api_client import (
    ArtistCategories,
    ArtistOptionalFields,
    ArtistRoles,
    ArtistRolesSet,
    ArtistType,
    ContentLanguagePreference,
)
from .vocadb_api_client.models import StrEnum

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from logging import Logger
    from typing import TypedDict

    from .vocadb_api_client import (
        ArtistApiApi,
        ArtistContract,
        ArtistForAlbumForApiContract,
        ArtistForApiContract,
        ArtistForSongContract,
        ArtistRolesSet,
        ContentLanguagePreference,
    )

    class ArtistInfoBase(TypedDict, total=False):
        artist: str
        artist_id: str | None
        artists: list[str] | None
        artist_ids: list[str] | None

    class ArtistInfo(ArtistInfoBase, closed=True): ...

    class AlbumArtistInfo(ArtistInfoBase, closed=True, total=False):
        label: str | None
        va: bool

    class TrackArtistInfo(ArtistInfoBase, closed=True, total=False):
        arrangers: list[str] | None
        arranger_ids: list[str] | None
        composers: list[str] | None
        composer_ids: list[str] | None
        lyricists: list[str] | None
        lyricist_ids: list[str] | None
        remixers: list[str] | None
        remixers_ids: list[str] | None


class ProcessedArtistCategories(StrEnum):
    PRODUCERS = auto()
    COMPOSERS = auto()
    ARRANGERS = auto()
    LYRICISTS = auto()
    CIRCLES = auto()
    VOCALISTS = auto()


class ArtistCategory:
    def __init__(self) -> None:
        self._names: list[str] = []
        self._ids: list[str] = []

    def add(self, name: str, id_: str) -> None:
        self._names.append(name)
        self._ids.append(id_)

    @property
    def names(self) -> list[str] | None:
        return self._names or None

    @property
    def ids(self) -> list[str] | None:
        return self._ids if any(self._ids) else None

    def items(self) -> zip[tuple[str, str]]:
        return zip(self._names, self._ids)

    def __iter__(self) -> Iterator[tuple[str, str]]:
        return iter(self.items())


class CategorizedArtists(
    dict[
        ProcessedArtistCategories,
        ArtistCategory,
    ]
):
    def __init__(self) -> None:
        # Initialize all expected keys
        super().__init__(
            {key: ArtistCategory() for key in ProcessedArtistCategories}
        )

    def _collect_unique_items(self, attr: str) -> list[str] | None:
        return (
            unique_items
            if (
                unique_items := unique_list(
                    elements=(
                        (
                            element
                            for category in self.values()
                            for element in cast(
                                list[str], getattr(category, attr) or []
                            )
                        )
                    )
                )
            )
            and any(unique_items)
            else None
        )

    @property
    def names(self) -> list[str] | None:
        return self._collect_unique_items("names")

    @property
    def ids(self) -> list[str] | None:
        # access attribute directly rather than the property
        # to preserve empty str values
        return self._collect_unique_items("_ids")


class ArtistsProcessor:
    def __init__(
        self,
        va_name: str,
        use_base_voicebank: bool,
        artist_api: ArtistApiApi,
        language_preference: ContentLanguagePreference,
        logger: Logger,
    ) -> None:
        self.va_name: str = va_name
        self.use_base_voicebank: bool = use_base_voicebank
        self.artist_api: ArtistApiApi = artist_api
        self.language_preference: ContentLanguagePreference = (
            language_preference
        )
        self._log: Logger = logger

    def get_album_artists(
        self,
        remote_artists: tuple[ArtistForAlbumForApiContract, ...] | None,
        is_comp: bool,
        include_featured_artists: bool = True,
    ) -> AlbumArtistInfo:
        if not remote_artists:
            return {
                "va": is_comp,
            }
        artists_by_categories: CategorizedArtists
        not_creditable_artists: frozenset[tuple[str, str]]
        artists_by_categories, not_creditable_artists = (
            self._categorize_artists(remote_artists=remote_artists)
        )
        artist_info: ArtistInfo = self._get_artists(
            artists_by_categories=artists_by_categories,
            not_creditable_artists=not_creditable_artists,
            include_featured_artists=include_featured_artists,
            comp=is_comp,
        )
        return {
            **artist_info,
            "label": self._get_label(remote_artists=remote_artists),
            "va": is_comp or (artist_info.get("artist") == self.va_name),
        }

    def get_track_artists(
        self,
        remote_artists: tuple[ArtistForSongContract, ...] | None,
        is_remix: bool,
        remote_original_artists: tuple[ArtistForSongContract, ...]
        | None = None,
    ) -> TrackArtistInfo:
        if not remote_artists:
            return {}
        artists_by_categories: CategorizedArtists
        not_creditable_artists: frozenset[tuple[str, str]]
        artists_by_categories, not_creditable_artists = (
            self._categorize_artists(remote_artists=remote_artists)
        )
        original_artists_by_categories: CategorizedArtists | None
        if remote_original_artists:
            original_artists_by_categories, _ = self._categorize_artists(
                remote_artists=remote_original_artists
            )
        else:
            original_artists_by_categories = None

        arrangers: list[str] | None = artists_by_categories[
            ProcessedArtistCategories.ARRANGERS
        ].names
        arranger_ids: list[str] | None = artists_by_categories[
            ProcessedArtistCategories.ARRANGERS
        ].ids

        remixers: list[str] | None
        remixers_ids: list[str] | None
        remixers, remixers_ids = (
            (arrangers, arranger_ids) if is_remix else (None, None)
        )

        if (
            original_artists_by_categories
            and original_artists_by_categories[
                ProcessedArtistCategories.COMPOSERS
            ]
        ):
            composers: list[str] | None = original_artists_by_categories[
                ProcessedArtistCategories.COMPOSERS
            ].names
            composer_ids: list[str] | None = original_artists_by_categories[
                ProcessedArtistCategories.COMPOSERS
            ].ids

        else:
            composers = artists_by_categories[
                ProcessedArtistCategories.COMPOSERS
            ].names
            composer_ids = artists_by_categories[
                ProcessedArtistCategories.COMPOSERS
            ].ids

        if (
            original_artists_by_categories
            and original_artists_by_categories[
                ProcessedArtistCategories.LYRICISTS
            ]
        ):
            lyricists: list[str] | None = original_artists_by_categories[
                ProcessedArtistCategories.LYRICISTS
            ].names
            lyricist_ids: list[str] | None = original_artists_by_categories[
                ProcessedArtistCategories.LYRICISTS
            ].ids

        else:
            lyricists = artists_by_categories[
                ProcessedArtistCategories.LYRICISTS
            ].names
            lyricist_ids = artists_by_categories[
                ProcessedArtistCategories.LYRICISTS
            ].ids

        return {
            **self._get_artists(
                artists_by_categories=artists_by_categories,
                not_creditable_artists=not_creditable_artists,
                comp=False,
                include_featured_artists=True,
            ),
            "arrangers": arrangers,
            "arranger_ids": arranger_ids,
            "composers": composers,
            "composer_ids": composer_ids,
            "lyricists": lyricists,
            "lyricist_ids": lyricist_ids,
            "remixers": remixers,
            "remixers_ids": remixers_ids,
        }

    @lru_cache(maxsize=128)
    def _categorize_artists(
        self,
        remote_artists: tuple[ArtistForAlbumForApiContract, ...]
        | tuple[ArtistForSongContract, ...],
    ) -> tuple[CategorizedArtists, frozenset[tuple[str, str]]]:
        """Categorizes artists by their roles and identifies not creditable artists.

        Takes a list of artists and organizes them into categories like producers,
        circles, vocalists, etc. based on their roles and categories.
        Also identifies which artists are not creditable.

        Args:
            remote_artists: List of AlbumArtist or SongArtist objects to categorize

        Returns:
            Tuple containing:
            - ArtistsByCategories object with artists sorted into role categories
            - Set of tuples of artist ids and names that are not creditable
        """
        artists_by_categories: CategorizedArtists = CategorizedArtists()
        not_creditable_artists: set[tuple[str, str]] = set()

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

        remote_album_or_song_artist: (
            ArtistForAlbumForApiContract | ArtistForSongContract
        )
        for remote_album_or_song_artist in remote_artists:
            remote_artist: ArtistContract | ArtistForApiContract | None
            if (
                (remote_artist := remote_album_or_song_artist.artist)
                and self.use_base_voicebank
                and (remote_artist.artist_type in ArtistType.any_vocal_synth())
                and (
                    remote_artist := self.get_base_voicebank(
                        voicebank=remote_artist
                    )
                )
            ):
                name: str | None = (
                    name.removesuffix(" (Unknown)")
                    if (name := remote_artist.name)
                    else None
                )
                id_: str = str(remote_artist.id)
            else:
                name, id_ = (
                    (
                        remote_album_or_song_artist.name or remote_artist.name,
                        str(remote_artist.id),
                    )
                    if remote_artist
                    else (remote_album_or_song_artist.name, "")
                )
            if not name:
                continue
            if remote_album_or_song_artist.is_support or any(
                {
                    ArtistCategories.NOTHING,
                    ArtistCategories.LABEL,
                }
                & remote_album_or_song_artist.categories
            ):
                not_creditable_artists.add((name, id_))

            # Handle producers/bands first
            effective_roles: ArtistRolesSet = (
                remote_album_or_song_artist.effective_roles
            )
            if {
                ArtistCategories.PRODUCER,
                # ArtistCategories.CIRCLE,
                ArtistCategories.BAND,
            } & remote_album_or_song_artist.categories:
                if "Default" in remote_album_or_song_artist.effective_roles:
                    effective_roles |= producer_roles
                artists_by_categories[ProcessedArtistCategories.PRODUCERS].add(
                    name, id_
                )

            # Apply role/category mappings
            remote_role: ArtistCategories | ArtistRoles
            category: ProcessedArtistCategories
            for remote_role, category in role_category_map.items():
                if (
                    isinstance(remote_role, ArtistCategories)
                    and remote_role in remote_album_or_song_artist.categories
                ) or remote_role in effective_roles:
                    artists_by_categories[category].add(name, id_)

        # Set producer fallbacks if needed
        if (
            artists_by_categories[ProcessedArtistCategories.VOCALISTS]
            and not artists_by_categories[ProcessedArtistCategories.PRODUCERS]
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
            if not artists_by_categories[category].names:
                artists_by_categories[category] = artists_by_categories[
                    ProcessedArtistCategories.PRODUCERS
                ]

        return artists_by_categories, frozenset(not_creditable_artists)

    @cache
    def get_base_voicebank(
        self, voicebank: ArtistContract | ArtistForApiContract
    ) -> ArtistForApiContract | ArtistContract:
        remote_full_artist: ArtistForApiContract | ArtistContract | None
        base_voicebank: ArtistContract | None
        if (
            remote_full_artist := self.artist_api.api_artists_id_get(
                id_=voicebank.id,
                fields=(ArtistOptionalFields.BASE_VOICEBANK,),
                lang=self.language_preference,
            )
        ) and (base_voicebank := remote_full_artist.base_voicebank):
            self._log.debug(
                msg=f'Voicebank "{voicebank.name}" with id '
                + f"{voicebank.id} is a derivative of "
                + f"the voicebank {base_voicebank.name} with id "
                + f"{base_voicebank.id}."
            )
            return self.get_base_voicebank(voicebank=base_voicebank)
        return voicebank

    def _get_artists(
        self,
        artists_by_categories: CategorizedArtists,
        not_creditable_artists: frozenset[tuple[str, str]],
        comp: bool,
        include_featured_artists: bool,
    ) -> ArtistInfo:
        def get_filtered_artists(
            *categories: ProcessedArtistCategories,
        ) -> list[str]:
            return [
                name
                for category in categories
                for name, id in artists_by_categories[category]
                if (name, id) not in not_creditable_artists
            ]

        if comp:
            main_artists: list[str] = [self.va_name]
        else:
            if not (
                main_artists := get_filtered_artists(
                    ProcessedArtistCategories.PRODUCERS,
                    ProcessedArtistCategories.CIRCLES,
                )
            ):
                main_artists = get_filtered_artists(
                    ProcessedArtistCategories.VOCALISTS
                )

        if (
            include_featured_artists
            and artists_by_categories[ProcessedArtistCategories.VOCALISTS]
            and (comp or main_artists)
        ):
            featured_artists: list[str] = get_filtered_artists(
                ProcessedArtistCategories.VOCALISTS
            )
        else:
            featured_artists = []

        if len(main_artists) > 5:
            artist_string: str = self.va_name
        else:

            def create_artists_dict_list(
                artists: list[str],
            ) -> list[dict[str | int, str]]:
                return [{"name": artist, "id": ""} for artist in artists]

            artists_dict_list: list[dict[str | int, str]] = (
                create_artists_dict_list(artists=main_artists)
            )
            join_key: str = "join"
            artists_dict_list[-1][join_key] = "feat."

            if len(main_artists + featured_artists) <= 5:
                artists_dict_list += create_artists_dict_list(
                    artists=featured_artists
                )
            artist_string, _ = MetadataSourcePlugin.get_artist(
                artists=artists_dict_list,
                join_key=join_key,
            )

        artists_names: list[str] | None = artists_by_categories.names
        artists_ids: list[str] | None = artists_by_categories.ids
        artist_id: str | None = None
        if artists_ids:
            if artists_names:
                for artist in main_artists + featured_artists:
                    with suppress(IndexError, ValueError):
                        if artist_id := artists_ids[
                            artists_names.index(artist)
                        ]:
                            break
            if not artist_id:
                artist_id = next(filter(None, artists_ids), None)

        return {
            "artist": artist_string,
            "artist_id": artist_id,
            "artists": artists_names,
            "artist_ids": artists_ids,
        }

    @staticmethod
    def _get_label(
        remote_artists: Iterable[ArtistForAlbumForApiContract] | None,
    ) -> str | None:
        labels: list[str] = []
        circles: list[str] = []
        for remote_albumartist in remote_artists or ():
            if filtered_categories := remote_albumartist.categories & {
                ArtistCategories.LABEL,
                ArtistCategories.CIRCLE,
            }:
                if (
                    not remote_albumartist.is_support
                    and remote_albumartist.name
                ):
                    if ArtistCategories.LABEL in filtered_categories:
                        labels.append(remote_albumartist.name)
                        continue
                    circles.append(remote_albumartist.name)
        return ", ".join(labels or circles) or None
