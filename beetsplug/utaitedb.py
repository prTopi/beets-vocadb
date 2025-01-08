from . import vocadb
from .vocadb.requests_handler import RequestsHandler


class UtaiteDBRequestsHandler(
    RequestsHandler,
    base_url="https://utaitedb.net/api/",
): ...


class UtaiteDBPlugin(
    vocadb.VocaDBPlugin,
    requests_handler=UtaiteDBRequestsHandler,
    data_source="UtaiteDB",
    base_url="https://utaitedb.net/",
    subcommand="udbsync",
): ...
