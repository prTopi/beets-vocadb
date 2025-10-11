from beetsplug.vocadb.abc import PluginABCs


class VocaDBPlugin(
    PluginABCs.PluginABC,
    base_url="https://vocadb.net/",
    api_url="https://vocadb.net/api/",
    subcommand="vdbsync",
): ...
