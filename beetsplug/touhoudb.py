from beetsplug.vocadb.abc import (
    PluginABCs,  # can safely import the class now ig
)


class TouhouDBPlugin(
    PluginABCs.PluginABC,
    base_url="https://touhoudb.com/",
    api_url="https://touhoudb.com/api/",
    subcommand="tdbsync",
): ...
