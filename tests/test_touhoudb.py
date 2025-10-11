from beetsplug.touhoudb import TouhouDBPlugin
from tests.abc import TestABC


class TestTouhouDBPlugin(
    TestABC,
    plugin=TouhouDBPlugin(),
): ...
