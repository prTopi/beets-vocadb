# Define package exports
__all__ = ["AlbumApiApi", "SongApiApi"]

# import apis into api package
from .album_api_api import AlbumApiApi as AlbumApiApi
from .song_api_api import SongApiApi as SongApiApi
