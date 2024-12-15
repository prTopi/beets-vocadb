from beetsplug.utaitedb import UtaiteDBPlugin
from tests.test_vocadb import TestVocaDBPlugin

class TestUtaiteDBPlugin(TestVocaDBPlugin):
    def setUp(self):
        self.plugin = UtaiteDBPlugin()
