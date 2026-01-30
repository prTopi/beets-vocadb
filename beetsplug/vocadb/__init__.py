from beetsplug.vocadb.base import PluginBase


class VocaDBPlugin(
    PluginBase,
    base_url="https://vocadb.net/",
    api_url="https://vocadb.net/api/",
    subcommand_prefix="vdb",
): ...
