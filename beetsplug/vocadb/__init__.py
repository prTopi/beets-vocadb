from beetsplug.vocadb.abc import PluginABC


class VocaDBPlugin(
    PluginABC,
    base_url="https://vocadb.net/",
    api_url="https://vocadb.net/api/",
    subcommand="vdbsync",
): ...
