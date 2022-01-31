"""A package to create and use app specific settings with type hints."""

__version__ = "0.2-post1"

from ._lib import typed_settings_prefix, typed_settings_dict, UndefinedValue, undefined

__all__ = "typed_settings_prefix", "typed_settings_dict", "UndefinedValue", "undefined"
