from beetsplug.vocadb import VocaDBPlugin, VocaDBInstance


class TouhouDBPlugin(
    VocaDBPlugin,
    instance=VocaDBInstance(
        name="TouhouDB",
        base_url="https://touhoudb.com/",
        api_url="https://touhoudb.com/api/",
        subcommand="tdbsync",
    ),
): ...
