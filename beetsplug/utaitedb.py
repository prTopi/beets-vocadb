from beetsplug.vocadb import VocaDBPlugin

class UtaiteDBPlugin(VocaDBPlugin):
    def __init__(self):
        super().__init__()
        self.data_source = "UtaiteDB"
        self.base_url = "https://utaiteadb.net/"
        self.api_url = "https://utaitedb.net/api/"
        self.subcommand = "udbsync"
