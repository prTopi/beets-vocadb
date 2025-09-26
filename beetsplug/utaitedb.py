from beetsplug import vocadb


class UtaiteDBPlugin(
    vocadb.VocaDBPlugin,
    base_url="https://utaitedb.net/",
    api_url="https://utaitedb.net/api/",
    subcommand="udbsync",
): ...
