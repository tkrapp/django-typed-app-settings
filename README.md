# typed_app_settings

A small django module for app specific settings (using type annotations).

## Why another app settings module for Django?

With other existing approaches to make your reusable django apps configurable
using the global project's `settings.py` file, it is not possible to get proper
IDE support including type checking.

This module aims to provide IDE support (mainly auto completion) and static type
checking (for example with mypy or pylance).

## Installation

Installation is easy. Just `pip install` the module like so:

```bash
pip install typed-app-settings
```

## Usage

1. Define a settings class in your app folder

   ```python
   # my_app/conf.py
   from typed_app_settings import typed_app_settings_prefix, undefined

   @typed_app_settings_prefix("MY_APP")  # see below for the two alternative decorators
   class Settings:
       SOME_STRING: str = "This is a cool string!"
       SOME_NUMBER: int = 30
       SOME_URL: str = undefined()

   settings = Settings()
   ```

2. Override some settings in your global `settings.py`

   ```python
   # my_project/settings.py
   MY_APP_SOME_URL = "http://example.com"
   MY_APP_SOME_NUMBER = 42
   ```

3. Use the settings in your `views.py` or elsewhere

   ```python
   # my_app/views.py
   from somewhere import fetch_url

   from .conf import settings

   def my_cool_view(request):
       ...
       content = fetch_url(settings.SOME_URL)
       ...
   ```

## Available decorators

You can choose between two styles of decorators which only differ in the way
they look up overridden values in the project's `settings.py` file.

### typed_app_settings_prefix

With this decorator, you define a prefix which is used to override settings
in `settings.py`.

**Example**:

```python
# my_app/conf.py
from typed_app_settings import typed_app_settings_prefix

@typed_app_settings_prefix("MY_APP")
class Settings:
    SOME_STR: str = "default value"
    SOME_NUMBER: int = 10
```

```python
# my_project/settings.py
...
MY_APP_SOME_STR = "default value"
MY_APP_SOME_NUMBER = 20
...
```

### typed_app_settings_dict

With this decorator, you define a dictionary which is resides in your `settings.py`
and is used to override settings.

**Example**:

```python
# my_app/conf.py
from typed_app_settings import typed_app_settings_dict

@typed_app_settings_dict("MY_APP")
class Settings:
    SOME_STR: str = "default value"
    SOME_NUMBER: int = 10
```

```python
# my_project/settings.py
...
MY_APP = {
    "SOME_STR": "default value",
    "SOME_NUMBER": 20,
}
...
```

## Functions

### undefined

This function is used to indicate that a setting must be configured in your `settings.py`.

```python
from typed_apps_settings import typed_app_settings_prefix, undefined

@typed_app_settings_prefix("MY_APP")
class Settings:
    ...
    THIS_MUST_BE_CONFIGURED: str = undefined()
    ...

settings = Settings()

settings.THIS_MUST_BE_CONFIGURED  # raises ImproperlyConfigured when no setting
                                  # is provided in settings.py
```

## Automatic imports

There is some magic implemented when using "special" type annotations.

### Automatic module loading

If a setting is annotated with `types.ModuleType` and an override of type `str`
is provided in `settings.py`, then this override is treated as a path to a module
which is imported on first attribute access.

**Example**:

```python
# my_app/conf.py
from types import ModuleType

from typed_apps_settings import typed_app_settings_prefix

from . import forms

@typed_app_settings_prefix("MY_APP")
class Settings:
    ...
    FORMS: ModuleType = forms  # it is important to reference the default module
                               # directly, so that mypy and pylance do not complain
    ...

settings = Settings()
```

```python
# my_project/settings.py
...
MY_APP_FORMS = "path.to.other.forms"
```

```python
# my_app/views.py
from .conf import settings

def my_view(request):
    ...
    form = settings.FORMS.CustomerForm(request.POST)
    ...
```

### Automatic class loading

If a setting is annotated with `typing.Type` or `type` and an override of type `str`
is provided in `settings.py`, then this override is treated as a path to a class
which is imported on first attribute access.

**Note**: This behaviour is similar to automatic module loading, except it returns
a class instead of a module.

**Example**:

```python
# my_app/conf.py
import typing

from typed_apps_settings import typed_app_settings_prefix

from .forms import CustomerForm

@typed_app_settings_prefix("MY_APP")
class Settings:
    ...
    CUSTOMER_FORM: typing.Type = CustomerForm  # it is important to define the default class
                                               # directly, so that mypy and pylance do not complain
    ...

settings = Settings()
```

```python
# my_project/settings.py
...
MY_APP_CUSTOMER_FORM = "path.to.other.forms.CustomerForm"
```

```python
# my_app/views.py
from .conf import settings

def my_view(request):
    ...
    form = settings.CUSTOMER_FORM(request.POST)
    ...
```

## Caveats

### No runtime type checking (right now)

In the current version, there is no automatic runtime type checking, but it may
be implemented in a future version.

## Changelog

### 0.1

- Initial release

### 0.1-post1

- Update classifiers

### 0.2

- Add function `undefined` which provides better IDE support.
  The class `UndefinedValue` should not be instantiated directly and may be
  changed or even removed in the future.
- Update README
- Update classifiers
