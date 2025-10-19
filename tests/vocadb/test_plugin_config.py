import pytest

from beetsplug.vocadb.plugin_config import InstanceConfig


class TestInstanceConfig:
    @pytest.mark.parametrize(
        argnames="prefer_romaji, languages, expected",
        argvalues=[
            (False, ["en", "jp"], "English"),
            (False, ["jp", "en"], "Japanese"),
            (True, ["jp", "en"], "Romaji"),
            (True, ["en", "jp"], "English"),
            (True, None, "Default"),
        ],
    )
    def test_get_lang(
        self, prefer_romaji: bool, languages: list[str], expected: str
    ) -> None:
        assert (
            InstanceConfig.get_lang(
                prefer_romaji=prefer_romaji, languages=languages
            )
            == expected
        )
