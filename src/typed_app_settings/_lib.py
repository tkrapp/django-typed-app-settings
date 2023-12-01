import importlib
import inspect
import sys
import types
from typing import Any, Callable, Type, TypeVar, cast

from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured

if sys.version_info >= (3, 10):
    get_annotations = inspect.get_annotations
else:
    from ._get_annotations import get_annotations

    get_annotations = get_annotations

_T = TypeVar("_T")
_ATTR_RESOLVED_POSTFIX = "__resolved"
_CLASS_DECORATOR = Callable[[Type[_T]], Type[_T]]


class _SettingNotFoundError(Exception):
    pass


class UndefinedValue:
    """
    Should be used for configuration attributes which must be defined in the global
    settings module.
    """

    def __set_name__(self, owner: Type[object], name: str):
        self.name = name

    def __raise(self):
        raise ImproperlyConfigured(f"The attribute {self.name} is not configured")

    def __eq__(self, _other: Any):
        return self.__raise()

    def __bool__(self):
        return self.__raise()

    def __str__(self):
        return self.__raise()

    def __repr__(self):
        return f"<{type(self).__name__}: {self.name}>"


def _import_module(path: str, /) -> types.ModuleType:
    """Import a module from a provided path."""
    package, _, module_name = path.rpartition(".")

    return importlib.import_module(name=module_name, package=package)


def _import_class(path: str, /) -> Type[object]:
    """Import a class from a provided path."""
    module_path, _, class_name = path.rpartition(".")
    package, _, module_name = module_path.rpartition(".")
    module = importlib.import_module(name=module_name, package=package)

    return cast(Type[object], getattr(module, class_name))


def _raise_on_set_attribute(self: object, attr_name: str, value: Any):
    """
    Raise AttributeError when an attribute is set on the settings instance.
    Except the attr_name ends with _ATTR_RESOLVED_POSTFIX.
    """
    if not attr_name.endswith(_ATTR_RESOLVED_POSTFIX):
        raise AttributeError(f"Can't set attribute {attr_name}")
    self.__dict__[attr_name] = value


def _check_module(annotation: Any) -> bool:
    """Check if the annotation is ModuleType"""
    return annotation is types.ModuleType


def _check_type(annotation: Any) -> bool:
    """Check if the annotation represents a class/Type"""

    if (
        getattr(annotation, "__qualname__", None) == "type"
        and getattr(annotation, "__module__", None) == "builtins"
    ):
        # Check for something like 'type[...]'
        return True
    elif (
        getattr(annotation, "_name", None) == "Type"
        and getattr(annotation, "__module__", None) == "typing"
    ):
        # Check for something like 'typing.Type[...]'
        return True
    return False


def _typed_settings_decorator(
    django_settings_getter: Callable[[str], Any]
) -> _CLASS_DECORATOR[_T]:
    def _class_decorator(cls: Type[_T]) -> Type[_T]:
        type_hints = get_annotations(cls)

        for attr_name, value in inspect.getmembers(cls):
            # Skip dunder attributes and methods.
            if (
                attr_name.startswith("__") and attr_name.endswith("__")
            ) or not attr_name.isupper():
                continue

            # Define names for the "real" attribute and the resolved value
            hidden_attr_name = f"_{attr_name}"
            resolved_attr_name = f"_{attr_name}{_ATTR_RESOLVED_POSTFIX}"

            # Property getter which substitutes the class member and handles
            # overriding of settings via settings.py.
            def getter(
                self: object,
                attr_name: str = attr_name,
                hidden_attr_name: str = hidden_attr_name,
                resolved_attr_name: str = resolved_attr_name,
            ) -> Any:
                # Check if the setting was resolved previously and return that
                # already resolved value.
                value = getattr(self, resolved_attr_name)
                if value is not UndefinedValue:
                    return value

                annotation = type_hints.get(attr_name)
                # Check if the setting is overridden via settings.py.
                try:
                    value = django_settings_getter(attr_name)
                except _SettingNotFoundError:
                    value = getattr(self, hidden_attr_name)

                # Perform checks and "magical" behaviours.
                if isinstance(value, UndefinedValue):
                    raise ImproperlyConfigured(
                        f"{attr_name!r} needs to be configured in your settings module"
                    )
                elif _check_module(annotation) and isinstance(value, str):
                    value = _import_module(value)
                elif _check_type(annotation) and isinstance(value, str):
                    value = _import_class(value)

                # Store the resolved setting in the instance.
                setattr(self, resolved_attr_name, value)

                return value

            def setter(self: object, value: Any, attr_name: str = attr_name):
                raise AttributeError(f"Can't set attribute '{attr_name}'")

            prop = property(getter, setter)

            setattr(cls, resolved_attr_name, UndefinedValue)
            setattr(cls, hidden_attr_name, value)
            setattr(cls, attr_name, prop)
            setattr(cls, "__setattr__", _raise_on_set_attribute)
        return cls

    return _class_decorator


def typed_settings_prefix(prefix: str) -> _CLASS_DECORATOR[_T]:
    """
    Class decorator which transforms all attributes of the decorated class
    into properties which perform the required lookups in the django settings
    module.

    Example:
    # The project's settings.py
    MYAPP_SOME_STRING = "some string override"

    >>> import types
    >>> import os
    >>> import collections
    >>> @typed_settings_prefix("MYAPP")
    ... class MyAppSettings:
    ...     SOME_STRING: str = "some string"
    ...     SOME_MODULE: types.ModuleType = os
    ...     SOME_CLASS: Type = collections.deque
    >>> settings = MyAppSettings()
    >>> print(settings.SOME_STRING)
    "some string override"
    >>> settings.SOME_MODULE
    <module 'os' from '...'>
    """

    if prefix.endswith("_"):
        raise ValueError("'prefix' must not end with '_'")

    def django_settings_getter(attr_name: str) -> Any:
        try:
            return getattr(django_settings, f"{prefix}_{attr_name}")
        except AttributeError:
            raise _SettingNotFoundError()

    return _typed_settings_decorator(django_settings_getter)


def typed_settings_dict(settings_attr: str) -> _CLASS_DECORATOR[_T]:
    """
    Class decorator which transforms all attributes of the decorated class
    into properties which perform the required lookups in the django settings
    module.

    Example:
    # The project's settings.py
    MYAPP = {
        "SOME_STRING": "some string override",
    }

    >>> import types
    >>> import os
    >>> import collections
    >>> @typed_settings_dict("MYAPP")
    ... class MyAppSettings:
    ...     SOME_STRING: str = "some string"
    ...     SOME_MODULE: types.ModuleType = os
    ...     SOME_CLASS: Type = collections.deque
    >>> settings = MyAppSettings()
    >>> print(settings.SOME_STRING)
    "some string override"
    >>> settings.SOME_MODULE
    <module 'os' from '...'>
    """

    settings_dict = getattr(django_settings, settings_attr, None)

    def django_settings_getter(attr_name: str) -> Any:
        if settings_dict and attr_name in settings_dict:
            return settings_dict[attr_name]
        raise _SettingNotFoundError()

    return _typed_settings_decorator(django_settings_getter)


def undefined() -> Any:
    """
    Mark a property as undefined so it needs to be defined in the project's settings.py
    """
    return UndefinedValue()
