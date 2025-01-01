from beetsplug.utaitedb import UtaiteDBPlugin
from tests import test_vocadb


class TestUtaiteDBPlugin(
    test_vocadb.TestVocaDBPlugin,
    plugin=UtaiteDBPlugin()
): ...
