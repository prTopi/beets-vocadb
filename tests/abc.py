import abc
from unittest import TestCase

from beetsplug.vocadb.base import PluginBases


class TestABC(TestCase, metaclass=abc.ABCMeta):
    __test__: bool = False
    plugin: PluginBases.PluginBase

    def __init_subclass__(cls, plugin: PluginBases.PluginBase) -> None:
        super().__init_subclass__()
        cls.__test__ = True
        cls.plugin = plugin
