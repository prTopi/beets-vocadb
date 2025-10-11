from beetsplug.utaitedb import UtaiteDBPlugin
from tests.abc import TestABC


class TestUtaiteDBPlugin(
    TestABC,
    plugin=UtaiteDBPlugin(),
): ...
