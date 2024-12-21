from beetsplug.touhoudb import TouhouDBPlugin
from tests.test_vocadb import TestVocaDBPlugin


class TestTouhouDBPlugin(TestVocaDBPlugin, plugin=TouhouDBPlugin()): ...
