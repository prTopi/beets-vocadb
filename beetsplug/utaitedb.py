from beetsplug.vocadb.abc import PluginABCs


class UtaiteDBPlugin(
    PluginABCs.PluginABC,
    base_url="https://utaitedb.net/",
    api_url="https://utaitedb.net/api/",
    subcommand="udbsync",
): ...
