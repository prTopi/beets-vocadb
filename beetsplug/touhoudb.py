from beetsplug.vocadb import VocaDBPlugin, InstanceInfo


class TouhouDBPlugin(
    VocaDBPlugin,
    instance_info=InstanceInfo(
        name="TouhouDB",
        base_url="https://touhoudb.com/",
        api_url="https://touhoudb.com/api/",
        subcommand="tdbsync",
    ),
): ...
