from __future__ import annotations

from collections.abc import Callable
from itertools import groupby
from operator import attrgetter
from re import match, search
from typing import TYPE_CHECKING, cast

from .vocadb_api_client import (
    AlbumDiscPropertiesContract,
    ContentLanguagePreference,
    DiscMediaType,
    SongInAlbumForApiContract,
)

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable

    from .vocadb_api_client import (
        TagBaseContract,
        TagUsageForApiContract,
        WebLinkForApiContract,
    )


def get_language_preference(
    prefer_romaji: bool, languages: Iterable[str] | None
) -> ContentLanguagePreference:
    if languages:
        for language in languages:
            match language:
                case "jp":
                    return (
                        ContentLanguagePreference.ROMAJI
                        if prefer_romaji
                        else ContentLanguagePreference.JAPANESE
                    )
                case "en":
                    return ContentLanguagePreference.ENGLISH
                case _:
                    ...

    return ContentLanguagePreference.DEFAULT


def discs_fallback(
    disc_total: int,
) -> tuple[AlbumDiscPropertiesContract, ...]:
    """Create default disc properties for albums without disc information.

    Args:
        disc_total: Number of discs in the album

    Returns:
        List of default disc properties
    """
    return tuple(
        AlbumDiscPropertiesContract(
            disc_number=i + 1,
            id=0,
            name="CD",
            media_type=DiscMediaType.AUDIO,
        )
        for i in range(disc_total)
    )


def get_asin(
    web_links: Iterable[WebLinkForApiContract] | None,
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


def normalize_bpm(milli_bpm: int | None) -> str | None:
    """Convert milli-BPM (beats per minute) to standard BPM format.

    VocaDB stores BPM values in milli-beats per minute (mBPM), so this
    method converts them to standard BPM by dividing by 1000.

    Args:
        max_milli_bpm: BPM value in milli-beats per minute

    Returns:
        BPM as string or None if input is None
    """
    return str(milli_bpm // 1000) if milli_bpm else None


def get_genres(
    remote_tags: Iterable[TagUsageForApiContract] | None,
) -> list[str] | None:
    """Extract and format genre information from VocaDB tags.

    Processes VocaDB tags to find those categorized as "Genres" and sorts them
    by usage count (most popular first).
    """
    if not remote_tags:
        return None
    genres: list[str] = []
    remote_tag_usage: TagUsageForApiContract
    for remote_tag_usage in sorted(
        remote_tags, key=lambda x: (-x.count, (x.tag.name or "").title())
    ):
        remote_tag: TagBaseContract = remote_tag_usage.tag
        if remote_tag.category_name == "Genres" and remote_tag.name:
            genres.append(remote_tag.name.title())
    return genres or None


def group_tracks_by_disc(
    remote_songs: Iterable[SongInAlbumForApiContract],
) -> dict[
    int, Collection[SongInAlbumForApiContract]
]:  # First sort by disc number
    tracks_by_disc: dict[
        int,
        Collection[SongInAlbumForApiContract],
    ] = {
        disc_number: tuple(songs_iter)
        for disc_number, songs_iter in groupby(
            remote_songs,
            key=cast(
                Callable[[SongInAlbumForApiContract], int],
                attrgetter("disc_number"),
            ),
        )
    }

    return tracks_by_disc
