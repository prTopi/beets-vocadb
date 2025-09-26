from beetsplug.touhoudb import TouhouDBPlugin
from tests import test_vocadb


class TestTouhouDBPlugin(
    test_vocadb.TestVocaDBPlugin,
    plugin=TouhouDBPlugin(),
): ...
