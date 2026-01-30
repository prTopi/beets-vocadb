from beetsplug.vocadb.base import PluginBase


class UtaiteDBPlugin(
    PluginBase,
    base_url="https://utaitedb.net/",
    api_url="https://utaitedb.net/api/",
    subcommand_prefix="udb",
): ...
