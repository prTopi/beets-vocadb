from beetsplug.vocadb import VocaDBPlugin, VocaDBInstance


class UtaiteDBPlugin(VocaDBPlugin):
    def __init__(self):
        super().__init__()
        self.instance = VocaDBInstance(
            name="UtaiteDB",
            base_url="https://utaiteadb.net/",
            api_url="https://utaitedb.net/api/",
            subcommand="udbsync",
        )
