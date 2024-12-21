from beetsplug.utaitedb import UtaiteDBPlugin
from tests.test_vocadb import TestVocaDBPlugin


class TestUtaiteDBPlugin(TestVocaDBPlugin, plugin=UtaiteDBPlugin()): ...
