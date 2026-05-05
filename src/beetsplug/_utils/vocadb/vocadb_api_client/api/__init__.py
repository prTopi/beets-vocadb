# Define package exports
__all__ = ["AlbumApiApi", "ArtistApiApi", "SongApiApi", "TagApiApi"]

# import apis into api package
from .album_api_api import AlbumApiApi as AlbumApiApi
from .artist_api_api import ArtistApiApi as ArtistApiApi
from .song_api_api import SongApiApi as SongApiApi
from .tag_api_api import TagApiApi as TagApiApi
