from beetsplug import vocadb


class UtaiteDBPlugin(
    vocadb.VocaDBPlugin,
    instance_info=vocadb.InstanceInfo(
        name="UtaiteDB",
        base_url="https://utaiteadb.net/",
        api_url="https://utaitedb.net/api/",
        subcommand="udbsync",
    ),
): ...
