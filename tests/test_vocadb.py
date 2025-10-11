from beetsplug.vocadb import VocaDBPlugin
from tests.abc import TestABC


class TestVocaDBPlugin(
    TestABC,
    plugin=VocaDBPlugin(),
): ...
