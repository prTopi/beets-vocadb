from __future__ import annotations

from typing import NamedTuple

import pytest
from httpx import URL

from beetsplug.vocadb.base import PluginBases


class InitSubclassTestCase(NamedTuple):
    cls_name: str
    base_url: URL | str
    api_url: URL | str
    subcommand_prefix: str
    expected_data_source: str
    expected_base_url: URL | str
    expected_api_url: URL | str
    expected_sync_subcommand: str


@pytest.mark.parametrize(
    argnames="test_case",
    argvalues=[
        InitSubclassTestCase(
            cls_name="FooPlugin",
            base_url="https://foo.net",
            api_url=URL("https://foo.net/api"),
            subcommand_prefix="foo",
            expected_data_source="Foo",
            expected_base_url=URL("https://foo.net"),
            expected_api_url="https://foo.net/api",
            expected_sync_subcommand="foosync",
        ),
        InitSubclassTestCase(
            cls_name="BarPlugin",
            base_url=URL("https://bar.com"),
            api_url="https://bar.com/api",
            subcommand_prefix="bar",
            expected_data_source="Bar",
            expected_base_url="https://bar.com",
            expected_api_url=URL("https://bar.com/api"),
            expected_sync_subcommand="barsync",
        ),
    ],
)
def test_init_subclass(
    test_case: InitSubclassTestCase,
) -> None:
    plugin_cls = type(
        test_case.cls_name,
        (PluginBases.PluginBase,),
        {},
        base_url=test_case.base_url,
        api_url=test_case.api_url,
        subcommand_prefix=test_case.subcommand_prefix,
    )
    plugin = plugin_cls()
    assert plugin.data_source == test_case.expected_data_source
    assert plugin.base_url == test_case.expected_base_url
    assert plugin.api_url == test_case.expected_api_url
    assert plugin.sync_subcommand == test_case.expected_sync_subcommand
