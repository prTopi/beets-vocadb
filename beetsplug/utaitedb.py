from beetsplug.vocadb import VocaDBPlugin, InstanceInfo


class UtaiteDBPlugin(
    VocaDBPlugin,
    instance_info=InstanceInfo(
        name="UtaiteDB",
        base_url="https://utaiteadb.net/",
        api_url="https://utaitedb.net/api/",
        subcommand="udbsync",
    ),
): ...
