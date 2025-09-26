from unittest import TestCase

from beetsplug.vocadb.plugin_config import InstanceConfig


class TestInstanceConfig(TestCase):
    instance_config: InstanceConfig = InstanceConfig()

    def test_get_lang(self) -> None:
        assert self.instance_config.get_lang(False, ["en", "jp"]) == "English"
        assert self.instance_config.get_lang(False, ["jp", "en"]) == "Japanese"
        assert self.instance_config.get_lang(True, ["jp", "en"]) == "Romaji"
        assert self.instance_config.get_lang(True, ["en", "jp"]) == "English"
        assert self.instance_config.get_lang(True, None) == "Default"
