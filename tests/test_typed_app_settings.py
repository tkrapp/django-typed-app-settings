import os
import pathlib
import types
import unittest
from collections import deque
from collections.abc import Sequence
from typing import Any, Type, Union

from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured

from typed_app_settings import typed_settings_dict, typed_settings_prefix, undefined

django_settings.configure(
    DEBUG=True,
    # MY_APP
    MY_APP_STR_SETTING_1="Setting 1 override",
    MY_APP_CLASS_SETTING_2="collections.deque",
    MY_APP_CLASS_SETTING_3=int,
    MY_APP_CLASS_SETTING_4="collections.deque",
    MY_APP_MODULE_SETTING_2="pathlib",
    MY_APP_UNCONFIGURED_OVERRIDE="Unconfigured override",
    # MY_SECOND_APP
    MY_SECOND_APP={
        "STR_SETTING_1": "Setting 1 override",
        "CLASS_SETTING_2": "collections.deque",
        "CLASS_SETTING_3": int,
        "CLASS_SETTING_4": "collections.deque",
        "MODULE_SETTING_2": "pathlib",
        "UNCONFIGURED_OVERRIDE": "Unconfigured override",
    },
)


class SomeBaseClass:
    def some_method(self) -> int:
        return 0


class SomeClass(SomeBaseClass):
    def some_method(self) -> int:
        return super().some_method() + 10


@typed_settings_prefix("MY_APP")
class PrefixSettings:
    STR_SETTING_1: str = "Setting 1"
    STR_SETTING_2: str = "Setting 2"
    CLASS_SETTING_1: Type[SomeBaseClass] = SomeClass
    CLASS_SETTING_2: Type[Sequence[Any]] = list
    CLASS_SETTING_3: Type[object] = str
    CLASS_SETTING_4: Type[object] = list
    MODULE_SETTING_1: types.ModuleType = os.path
    MODULE_SETTING_2: types.ModuleType = os.path
    UNCONFIGURED_OVERRIDE: str = undefined()
    UNCONFIGURED_SETTING: int = undefined()


@typed_settings_dict("MY_SECOND_APP")
class DictSettings:
    STR_SETTING_1: str = "Setting 1"
    STR_SETTING_2: str = "Setting 2"
    CLASS_SETTING_1: Type[SomeBaseClass] = SomeClass
    CLASS_SETTING_2: Type[Sequence[Any]] = list
    CLASS_SETTING_3: Type[object] = str
    CLASS_SETTING_4: Type[object] = list
    MODULE_SETTING_1: types.ModuleType = os.path
    MODULE_SETTING_2: types.ModuleType = os.path
    UNCONFIGURED_OVERRIDE: str = undefined()
    UNCONFIGURED_SETTING: int = undefined()


class Common:
    class TestCase(unittest.TestCase):
        settings: Union[PrefixSettings, DictSettings]

        def test_str_setting(self):
            self.assertEqual(self.settings.STR_SETTING_1, "Setting 1 override")

        def test_class_setting_1(self):
            self.assertIs(self.settings.CLASS_SETTING_1, SomeClass)

        def test_class_setting_2(self):
            self.assertIs(self.settings.CLASS_SETTING_2, deque)

        def test_class_setting_3(self):
            self.assertIs(self.settings.CLASS_SETTING_3, int)

        def test_class_setting_4(self):
            self.assertIs(self.settings.CLASS_SETTING_4, deque)

        def test_module_setting_1(self):
            self.assertIs(self.settings.MODULE_SETTING_1, os.path)

        def test_module_setting_2(self):
            self.assertIs(self.settings.MODULE_SETTING_2, pathlib)

        def test_unconfigured_setting_raising(self):
            with self.assertRaises(ImproperlyConfigured):
                self.settings.UNCONFIGURED_SETTING

        def test_unconfigured_setting_override(self):
            self.assertEqual(
                self.settings.UNCONFIGURED_OVERRIDE, "Unconfigured override"
            )


class TypedAppSettingsPrefix(Common.TestCase):
    def setUp(self):
        self.settings = PrefixSettings()


class TypedAppSettingsDict(Common.TestCase):
    def setUp(self):
        self.settings = DictSettings()


if __name__ == "__main__":
    unittest.main()
