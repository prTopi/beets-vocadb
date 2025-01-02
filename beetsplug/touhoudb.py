from . import vocadb
from .vocadb.api import InstanceInfo


class TouhouDBPlugin(
    vocadb.VocaDBPlugin,
    instance_info=InstanceInfo(
        name="TouhouDB",
        base_url="https://touhoudb.com/",
        api_url="https://touhoudb.com/api/",
        subcommand="tdbsync",
    ),
): ...
