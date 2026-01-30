from beetsplug.vocadb.base import PluginBase


class TouhouDBPlugin(
    PluginBase,
    base_url="https://touhoudb.com/",
    api_url="https://touhoudb.com/api/",
    subcommand_prefix="tdb",
): ...
