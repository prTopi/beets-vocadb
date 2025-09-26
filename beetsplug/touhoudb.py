from beetsplug import vocadb


class TouhouDBPlugin(
    vocadb.VocaDBPlugin,
    base_url="https://touhoudb.com/",
    api_url="https://touhoudb.com/api/",
    subcommand="tdbsync",
): ...
