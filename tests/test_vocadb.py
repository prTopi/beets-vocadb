from beetsplug.vocadb import VocaDBPlugin
from tests.abc import TestABC


class TestUtaiteDBPlugin(
    TestABC,
    plugin=VocaDBPlugin(),
): ...
