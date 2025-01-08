from . import vocadb
from .vocadb.requests_handler import RequestsHandler


class UtaiteDBRequestsHandler(
    RequestsHandler,
    base_url="https://touhoudb.com/api/",
): ...


class TouhouDBPlugin(
    vocadb.VocaDBPlugin,
    requests_handler=UtaiteDBRequestsHandler,
    data_source="TouhouDB",
    base_url="https://touhoudb.com/",
    subcommand="tdbsync",
): ...
