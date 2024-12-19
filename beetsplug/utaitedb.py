from beetsplug.vocadb import VocaDBPlugin, VocaDBInstance


class UtaiteDBPlugin(
    VocaDBPlugin,
    instance=VocaDBInstance(
        name="UtaiteDB",
        base_url="https://utaiteadb.net/",
        api_url="https://utaitedb.net/api/",
        subcommand="udbsync",
    ),
): ...
