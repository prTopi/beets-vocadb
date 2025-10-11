from beetsplug.vocadb.abc import PluginABCs


class TouhouDBPlugin(
    PluginABCs.PluginABC,
    base_url="https://touhoudb.com/",
    api_url="https://touhoudb.com/api/",
    subcommand="tdbsync",
): ...
