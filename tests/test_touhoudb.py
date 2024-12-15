from beetsplug.touhoudb import TouhouDBPlugin
from tests.test_vocadb import TestVocaDBPlugin

class TestTouhouDBPlugin(TestVocaDBPlugin):
    def setUp(self):
        self.plugin = TouhouDBPlugin()
