from beetsplug.vocadb.base import PluginBases


class TouhouDBPlugin(
    PluginBases.PluginBase,
    base_url="https://touhoudb.com/",
    api_url="https://touhoudb.com/api/",
    subcommand_prefix="tdb",
): ...
