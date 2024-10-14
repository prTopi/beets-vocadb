from beetsplug.utaitedb import UtaiteDBPlugin
from tests.test_vocadb import TestVocaDBPlugin

class TestUtaiteDBPlugin(TestVocaDBPlugin):
    def setUp(self):
        return super().setUp()
        self.plugin = UtaiteDBPlugin
