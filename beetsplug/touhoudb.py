from beetsplug.vocadb import VocaDBPlugin, VocaDBInstance


class TouhouDBPlugin(VocaDBPlugin):
    def __init__(self):
        super().__init__()
        self.data_source = "TouhouDB"
        self.instance = VocaDBInstance(
            base_url="https://touhoudb.com/",
            api_url="https://touhoudb.com/api/",
            subcommand="tdbsync"
        )
