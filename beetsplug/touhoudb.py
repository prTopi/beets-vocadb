from beetsplug import vocadb


class TouhouDBPlugin(
    vocadb.VocaDBPlugin,
    instance_info=vocadb.InstanceInfo(
        name="TouhouDB",
        base_url="https://touhoudb.com/",
        api_url="https://touhoudb.com/api/",
        subcommand="tdbsync",
    ),
): ...
