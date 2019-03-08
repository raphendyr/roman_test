try:
    # Python 3.7+
    from importlib.resources import (
        contents as _contents,
        is_resource as _is_resource,
        read_text as get_resource_text,
    )
except ImportError:
    # Backport for Python < 3.7
    from importlib_resources import (
        contents as _contents,
        is_resource as _is_resource,
        read_text as get_resource_text,
    )


def get_module_resources(module, extensions=None):
    files = _contents(module)
    if extensions:
        extensions = frozenset('.'+e.lstrip('.') for e in extensions)
        files = (fn for fn in files if any(fn.endswith(e) for e in extensions))
    return [fn for fn in files if _is_resource(module, fn)]
