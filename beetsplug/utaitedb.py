from beetsplug.vocadb.base import PluginBases


class UtaiteDBPlugin(
    PluginBases.PluginBase,
    base_url="https://utaitedb.net/",
    api_url="https://utaitedb.net/api/",
    subcommand="udbsync",
): ...
