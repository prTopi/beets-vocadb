from . import vocadb
from .vocadb.api import InstanceInfo


class UtaiteDBPlugin(
    vocadb.VocaDBPlugin,
    instance_info=InstanceInfo(
        name="UtaiteDB",
        base_url="https://utaiteadb.net/",
        api_url="https://utaitedb.net/api/",
        subcommand="udbsync",
    ),
): ...
