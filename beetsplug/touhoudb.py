from beetsplug.vocadb import VocaDBPlugin

class TouhouDBPlugin(VocaDBPlugin):
    def __init__(self):
        super().__init__()
        self.db_name = "TouhouDB"
        self.base_url = "https://touhoudb.com/"
        self.api_url = "https://touhoudb.com/api/"
        self.subcommand = "tdbsync"
