import beets
from beets.plugins import BeetsPlugin
from beets.ui import Subcommand

USER_AGENT = f"beets/{beets.__version__} +https://beets.io/"


class VocaDBPlugin(BeetsPlugin):
    def commands(self):
        vocadb_cmd = Subcommand("vocadb", help="vocadb testing command")

        def say_hi(lib, opts, args):
            print("Hello world!")

        vocadb_cmd.func = say_hi
        return [vocadb_cmd]
