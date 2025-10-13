from beetsplug.vocadb.abc import PluginABC


class TouhouDBPlugin(
    PluginABC,
    base_url="https://touhoudb.com/",
    api_url="https://touhoudb.com/api/",
    subcommand="tdbsync",
): ...
