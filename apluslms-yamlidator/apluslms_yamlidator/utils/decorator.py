from functools import update_wrapper


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
