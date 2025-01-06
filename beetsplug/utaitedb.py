from . import vocadb
from .vocadb.requests_handler import RequestsHandler


class UtaiteDBRequestsHandler(
    RequestsHandler,
    base_url="https://utaitedb.net/",
    api_url="https://utaitedb.net/api/",
): ...


class UtaiteDBPlugin(
    vocadb.VocaDBPlugin,
    requests_handler=UtaiteDBRequestsHandler,
    data_source="UtaiteDB",
    subcommand="udbsync",
): ...
