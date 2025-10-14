from beetsplug.vocadb.base import PluginBases


class VocaDBPlugin(
    PluginBases.PluginBase,
    base_url="https://vocadb.net/",
    api_url="https://vocadb.net/api/",
    subcommand="vdbsync",
): ...
