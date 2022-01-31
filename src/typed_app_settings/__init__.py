"""A package to create and use app specific settings with type hints."""

__version__ = "0.1-post2"

from ._lib import typed_settings_prefix, typed_settings_dict, UndefinedValue

__all__ = "typed_settings_prefix", "typed_settings_dict", "UndefinedValue"
