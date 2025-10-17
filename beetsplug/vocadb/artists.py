from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING

from beetsplug.vocadb.plugin_config import VA_NAME
from beetsplug.vocadb.vocadb_api_client import ArtistCategories, ArtistRoles
from beetsplug.vocadb.vocadb_api_client.models import StrEnum

if TYPE_CHECKING:
    from beetsplug.vocadb.vocadb_api_client import (
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


class CategorizedArtists(
    dict[
        ProcessedArtistCategories,
        list[tuple[str, str]],
    ]
):
    def __init__(self) -> None:
        # Initialize all expected keys
        super().__init__({key: [] for key in ProcessedArtistCategories})


def get_album_artists(
    remote_artists: list[ArtistForAlbumForApiContract] | None,
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
    not_creditable_artists: set[tuple[str, str]]
    artists_by_categories, not_creditable_artists = _categorize_artists(
        remote_artists
    )
    return (
        *_get_artists(
            artists_by_categories=artists_by_categories,
            not_creditable_artists=not_creditable_artists,
            include_featured_artists=include_featured_artists,
            comp=comp,
        ),
        _get_label(remote_artists=remote_artists),
    )


def get_track_artists(
    remote_artists: list[ArtistForSongContract] | None,
) -> tuple[
    str,
    str | None,
    list[str],
    list[str],
    str | None,
    str | None,
    str | None,
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
        - Arranger string
        - Composer string
        - Lyricist string
    """
    if not remote_artists:
        return "", None, [], [], "", "", ""
    artists_by_categories: CategorizedArtists
    not_creditable_artists: set[tuple[str, str]]
    artists_by_categories, not_creditable_artists = _categorize_artists(
        remote_artists
    )
    arranger, composer, lyricist = (
        ", ".join(name for name, _ in artists_by_categories[category]) or None
        for category in (
            ProcessedArtistCategories.ARRANGERS,
            ProcessedArtistCategories.COMPOSERS,
            ProcessedArtistCategories.LYRICISTS,
        )
    )
    return (
        *_get_artists(
            artists_by_categories=artists_by_categories,
            not_creditable_artists=not_creditable_artists,
            comp=False,
            include_featured_artists=True,
        ),
        arranger,
        composer,
        lyricist,
    )


def _categorize_artists(
    remote_artists: list[ArtistForAlbumForApiContract]
    | list[ArtistForSongContract],
) -> tuple[CategorizedArtists, set[tuple[str, str]]]:
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
        name: str | None
        id: str
        name, id = (
            (remote_artist.name, str(remote_artist.id))
            if (remote_artist := remote_album_or_song_artist.artist)
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
        if {
            ArtistCategories.PRODUCER,
            # ArtistCategories.CIRCLE,
            ArtistCategories.BAND,
        } & remote_album_or_song_artist.categories:
            if "Default" in remote_album_or_song_artist.effective_roles:
                remote_album_or_song_artist.effective_roles |= producer_roles
            artists_by_categories[ProcessedArtistCategories.PRODUCERS].append(
                (name, id)
            )

        # Apply role/category mappings
        remote_role: ArtistCategories | ArtistRoles
        category: ProcessedArtistCategories
        for remote_role, category in role_category_map.items():
            if (
                isinstance(remote_role, ArtistCategories)
                and remote_role in remote_album_or_song_artist.categories
            ) or remote_role in remote_album_or_song_artist.effective_roles:
                artists_by_categories[category].append((name, id))

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
        if not any(artists_by_categories[category]):
            artists_by_categories[category] = artists_by_categories[
                ProcessedArtistCategories.PRODUCERS
            ]

    return artists_by_categories, not_creditable_artists


def _get_artists(
    artists_by_categories: CategorizedArtists,
    not_creditable_artists: set[tuple[str, str]],
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

    main_artists: list[str] = [
        VA_NAME if comp else name
        for name, id in (
            *artists_by_categories[ProcessedArtistCategories.PRODUCERS],
            *artists_by_categories[ProcessedArtistCategories.CIRCLES],
        )
        if (name, id) not in not_creditable_artists
    ] or [
        name
        for name, id in artists_by_categories[
            ProcessedArtistCategories.VOCALISTS
        ]
        if (name, id) not in not_creditable_artists
    ]

    artist_string: str = (
        ", ".join(main_artists) if not len(main_artists) > 5 else VA_NAME
    )

    featured_artists: list[str] = []

    if (
        include_featured_artists
        and artists_by_categories[ProcessedArtistCategories.VOCALISTS]
        and (comp or main_artists)
    ):
        featured_artists.extend(
            name
            for name, id in artists_by_categories[
                ProcessedArtistCategories.VOCALISTS
            ]
            if (name, id) not in not_creditable_artists
        )
        if (
            featured_artists
            and not len(main_artists) + len(featured_artists) > 5
        ):
            artist_string += f" feat. {', '.join(featured_artists)}"

    artists_names: list[str]
    artists_ids: list[str]
    artists_names, artists_ids = _extract_artists_from_categories(
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
    )


def _extract_artists_from_categories(
    artist_by_categories: CategorizedArtists,
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

    category: list[tuple[str, str]]
    artists: dict[str, str] = {}

    for category in artist_by_categories.values():
        # Merge each category's artists into the dict while preserving order
        # and preventing duplicates
        artists |= category

    # Convert dict to separate lists of artists and IDs
    artists_names: list[str] = list(artists.keys())
    artists_ids: list[str] = list(artists.values())

    return artists_names, artists_ids


def _get_label(
    remote_artists: list[ArtistForAlbumForApiContract] | None,
) -> str | None:
    return next(
        (
            remote_albumartist.name
            for remote_albumartist in (remote_artists or [])
            if ArtistCategories.LABEL in remote_albumartist.categories
        ),
        None,
    )
