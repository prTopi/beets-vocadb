from __future__ import annotations

from collections import defaultdict
from re import match, search
from typing import TYPE_CHECKING

from beetsplug.vocadb.vocadb_api_client import (
    AlbumDiscPropertiesContract,
    DiscMediaType,
)

if TYPE_CHECKING:
    from beets.autotag.hooks import Info
    from beets.library import LibModel

    from beetsplug.vocadb.vocadb_api_client import (
        SongInAlbumForApiContract,
        TagBaseContract,
        TagUsageForApiContract,
        WebLinkForApiContract,
    )


def discs_fallback(
    disc_total: int,
) -> list[AlbumDiscPropertiesContract]:
    """Create default disc properties for albums without disc information.

    Args:
        disc_total: Number of discs in the album

    Returns:
        List of default disc properties
    """
    return [
        AlbumDiscPropertiesContract(
            disc_number=i + 1,
            id=0,
            name="CD",
            media_type=DiscMediaType.AUDIO,
        )
        for i in range(disc_total)
    ]


def get_asin(
    web_links: list[WebLinkForApiContract] | None,
) -> str | None:
    """Extract ASIN (Amazon Standard Identification Number) from web links."""
    return next(
        (
            asin_match[1]
            for link in (web_links or [])
            if not link.disabled
            and link.url
            and link.description
            and match(
                pattern=r"Amazon( ((LE|RE|JP|US)).*)?$",
                string=link.description,
            )
            and (
                asin_match := search(pattern=r"/dp/(.+?)(/|$)", string=link.url)
            )
        ),
        None,
    )


def get_bpm(max_milli_bpm: int | None) -> str | None:
    """Convert milli-BPM (beats per minute) to standard BPM format.

    VocaDB stores BPM values in milli-beats per minute (mBPM), so this
    method converts them to standard BPM by dividing by 1000.

    Args:
        max_milli_bpm: BPM value in milli-beats per minute

    Returns:
        BPM as string or None if input is None
    """
    return str(max_milli_bpm // 1000) if max_milli_bpm else None


def get_genres(remote_tags: list[TagUsageForApiContract]) -> str | None:
    """Extract and format genre information from VocaDB tags.

    Processes VocaDB tags to find those categorized as "Genres", sorts them
    by usage count (most popular first), and formats them as a semicolon-
    separated string with proper title casing.

    Args:
        remote_tags: List of tag usage data from VocaDB API

    Returns:
        Semicolon-separated genre string or None if no genres found
    """
    genres: list[str] = []
    remote_tag_usage: TagUsageForApiContract
    for remote_tag_usage in sorted(
        remote_tags, key=lambda x: x.count, reverse=True
    ):  # type: ignore[misc]
        remote_tag: TagBaseContract = remote_tag_usage.tag
        if remote_tag.category_name == "Genres" and remote_tag.name:
            genres.append(remote_tag.name.title())
    return "; ".join(genres) if genres else None


def get_id(
    entity: LibModel | Info,
    preferred_key: str,
    fallback_key: str,
) -> str | None:
    """Extract identifier from entity with fallback support.

    Attempts to retrieve an ID from the entity using the preferred key first,
    then falls back to the fallback key if the preferred key is not available
    or returns None.

    Args:
        entity: Entity to extract ID from (Item, Album, or TrackInfo)
        preferred_key: Primary key to check for ID
        fallback_key: Secondary key to check if preferred key fails

    Returns:
        ID as string or None if no ID found or empty
    """
    plugin_id: int | None = entity.get(  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        preferred_key
    )
    if plugin_id:
        return str(plugin_id)  # pyright: ignore[reportUnknownArgumentType]
    return entity.get(fallback_key) or None  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]


def group_tracks_by_disc(
    remote_songs: list[SongInAlbumForApiContract],
) -> dict[int, list[SongInAlbumForApiContract]]:
    tracks_by_disc: defaultdict[
        int,
        list[SongInAlbumForApiContract],
    ] = defaultdict(list)
    for remote_song in remote_songs:
        tracks_by_disc[remote_song.disc_number].append(remote_song)
    return tracks_by_disc
