from functools import update_wrapper
from importlib import import_module


def import_string(dotted_path):
    # Copied from Django project as is
    # source: django.utils.module_loading
    # url: https://github.com/django/django/blob/stable/2.0.x/django/utils/module_loading.py#L7
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" % dotted_path) from err

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError('Module "%s" does not define a "%s" attribute/class' % (
            module_path, class_name)
        ) from err


class cached_property(object):
    # Copied from Bottle project (Django has identical implementation)
    # source: bottle.cached_property
    # url: https://github.com/bottlepy/bottle/blob/release-0.12/bottle.py#L178
    """ A property that is only computed once per instance and then replaces
        itself with an ordinary attribute. Deleting the attribute resets the
        property. """

    def __init__(self, func):
        update_wrapper(self, func)
        self.func = func

    def __get__(self, obj, cls):
        if obj is None: return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value
