from beetsplug.vocadb.abc import PluginABC


class UtaiteDBPlugin(
    PluginABC,
    base_url="https://utaitedb.net/",
    api_url="https://utaitedb.net/api/",
    subcommand="udbsync",
): ...
