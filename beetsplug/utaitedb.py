from beetsplug.vocadb import VocaDBPlugin, VocaDBInstance


class UtaiteDBPlugin(VocaDBPlugin):
    def __init__(self):
        super().__init__()
        self.data_source = "UtaiteDB"
        self.instance = VocaDBInstance(
            base_url="https://utaiteadb.net/",
            api_url="https://utaitedb.net/api/",
            subcommand="udbsync"
        )
