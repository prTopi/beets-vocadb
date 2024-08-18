

class TouhouDBPlugin(VocaDBPlugin):
    def __init__(self):
        super(TouhouDBPlugin, self).__init__()
        self.name = "TouhouDB"
        self.base_url = "https://touhoudb.com/"
        self.api_url = "https://touhoudb.com/api/"
        self.subcommand = "tdbsync"
