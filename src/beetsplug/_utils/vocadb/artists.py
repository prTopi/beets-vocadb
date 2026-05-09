from __future__ import annotations

from collections.abc import Iterator
from contextlib import suppress
from enum import auto
from functools import cache, cached_property, lru_cache
from logging import Logger
from typing import TYPE_CHECKING, cast

from beets.metadata_plugins import MetadataSourcePlugin
from beets.util import unique_list

from .vocadb_api_client import (
    ArtistApiApi,
    ArtistCategories,
    ArtistContract,
    ArtistForApiContract,
    ArtistOptionalFields,
    ArtistOptionalFieldsSet,
    ArtistRoles,
    ArtistRolesSet,
    ContentLanguagePreference,
    TagApiApi,
    TagForApiContract,
    TagForApiContractPartialFindResult,
)
from .vocadb_api_client.models import StrEnum

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .vocadb_api_client import (
        ArtistForAlbumForApiContract,
        ArtistForSongContract,
    )


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

    def add(self, name: str, id: str) -> None:
        self._names.append(name)
        self._ids.append(id)

    @property
    def names(self) -> list[str] | None:
        return self._names or None

    @property
    def ids(self) -> list[str] | None:
        return self._ids or None

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

    def _collect_unique_items(self, attr: str) -> list[str]:
        return unique_list(
            item
            for category in self.values()
            for item in cast(list[str], getattr(category, attr) or [])
        )

    @property
    def names(self) -> list[str]:
        return self._collect_unique_items("names")

    @property
    def ids(self) -> list[str]:
        return self._collect_unique_items("ids")


class ArtistsProcessor:
    def __init__(
        self,
        va_name: str,
        use_base_voicebank: bool,
        artist_api: ArtistApiApi,
        tag_api: TagApiApi,
        language_preference: ContentLanguagePreference,
        logger: Logger,
    ) -> None:
        self.va_name: str = va_name
        self.use_base_voicebank: bool = use_base_voicebank
        self.artist_api: ArtistApiApi = artist_api
        self.tag_api: TagApiApi = tag_api
        self.language_preference: ContentLanguagePreference = (
            language_preference
        )
        self._log: Logger = logger

    @cached_property
    def voicebank_artist_types(self) -> set[str]:
        remote_tag_find_result: TagForApiContractPartialFindResult | None
        remote_tag_candidates: tuple[TagForApiContract, ...] | None
        id: int | None = None
        if (
            remote_tag_find_result := (
                self.tag_api.api_tags_get(
                    query="vocal synthesizer",
                    lang=self.language_preference,
                    maxResults=1,
                    preferAccurateMatches=True,
                )
            )
        ) and (remote_tag_candidates := remote_tag_find_result.items):
            with suppress(IndexError):
                id = remote_tag_candidates[0].id

        if not id:
            self._log.info('no "vocal synthesizer" tag found')
            return set()

        types = set(
            filter(
                None,
                (
                    child.name
                    for child in self.tag_api.api_tags_id_children_get(
                        id=id,
                        lang=self.language_preference,
                    )
                    or ()
                ),
            )
        )
        self._log.debug("Voicebank Artist Types: {}", types)
        return types

    def get_album_artists(
        self,
        remote_artists: tuple[ArtistForAlbumForApiContract, ...] | None,
        comp: bool,
        include_featured_artists: bool = True,
    ) -> tuple[
        str,
        str | None,
        list[str],
        list[str],
        str | None,
    ]:
        """Extract and format album artist information.

        Args:
            remote_artists: Artist data from VocaDB API
            comp: Whether this is a compilation album
            include_featured_artists: Whether to include featured artists
        Returns:
            Tuple containing:
            - Locally generated artist string
            - Artist ID of the first main artist
            or the first non-empty artist if available
            - List of unique artist names in order of first appearance
            - List of corresponding artist IDs in same order as artist names
            - Label string
        """
        if not remote_artists:
            return "", None, [], [], None
        artists_by_categories: CategorizedArtists
        not_creditable_artists: frozenset[tuple[str, str]]
        artists_by_categories, not_creditable_artists = (
            self._categorize_artists(remote_artists=remote_artists)
        )
        return (
            *self._get_artists(
                artists_by_categories=artists_by_categories,
                not_creditable_artists=not_creditable_artists,
                include_featured_artists=include_featured_artists,
                comp=comp,
            ),
            self._get_label(remote_artists=remote_artists),
        )

    def get_track_artists(
        self,
        remote_artists: tuple[ArtistForSongContract, ...] | None,
        remote_original_artists: tuple[ArtistForSongContract, ...]
        | None = None,
    ) -> tuple[
        str,
        str | None,
        list[str],
        list[str],
        list[str] | None,
        list[str] | None,
        list[str] | None,
        list[str] | None,
        list[str] | None,
        list[str] | None,
    ]:
        """
        Calls _get_artists with comp=False and include_featured_artists=True.

        Returns:
            Tuple containing:
            - Locally generated artist string
            - Artist ID of the first main artist
            or the first non-empty artist if available
            - List of unique artist names in order of first appearance
            - List of corresponding artist IDs in same order as artist names
            - Arrangers
            - Arrangers IDs
            - Composers
            - Composers IDs
            - Lyricists
            - Lyricists IDs
        """
        if not remote_artists:
            return (
                "",
                None,
                [],
                [],
                None,
                None,
                None,
                None,
                None,
                None,
            )
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

        return (
            *self._get_artists(
                artists_by_categories=artists_by_categories,
                not_creditable_artists=not_creditable_artists,
                comp=False,
                include_featured_artists=True,
            ),
            arrangers,
            arranger_ids,
            composers,
            composer_ids,
            lyricists,
            lyricist_ids,
        )

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
                and (
                    str(remote_artist.artist_type)
                    in self.voicebank_artist_types
                )
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
                id: str = str(remote_artist.id)
            else:
                name, id = (
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
                not_creditable_artists.add((name, id))

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
                    name, id
                )

            # Apply role/category mappings
            remote_role: ArtistCategories | ArtistRoles
            category: ProcessedArtistCategories
            for remote_role, category in role_category_map.items():
                if (
                    isinstance(remote_role, ArtistCategories)
                    and remote_role in remote_album_or_song_artist.categories
                ) or remote_role in effective_roles:
                    artists_by_categories[category].add(name, id)

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
                id=voicebank.id,
                fields=ArtistOptionalFieldsSet(
                    (ArtistOptionalFields.BASE_VOICEBANK,)
                ),
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
    ) -> tuple[str, str | None, list[str], list[str]]:
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

        artists_names: list[str] = artists_by_categories.names
        artists_ids: list[str] = artists_by_categories.ids
        artist_id: str | None = None
        for artist in main_artists + featured_artists:
            with suppress(IndexError, ValueError):
                if artist_id := artists_ids[artists_names.index(artist)]:
                    break
        if not artist_id:
            artist_id = next(filter(None, artists_ids), None)

        return (
            artist_string,
            artist_id,
            artists_names,
            artists_ids,
        )

    @staticmethod
    def _get_label(
        remote_artists: Iterable[ArtistForAlbumForApiContract] | None,
    ) -> str | None:
        return next(
            (
                remote_albumartist.name
                for remote_albumartist in (remote_artists or ())
                if ArtistCategories.LABEL in remote_albumartist.categories
            ),
            None,
        )
