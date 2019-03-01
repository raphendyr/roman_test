import sys
from collections import OrderedDict
from functools import wraps
from io import StringIO

import ruamel.yaml as ryaml

from .collections import ChangesDict, ChangesList


def _optional_stream(dumper):
    @wraps(dumper)
    def wrapper(documents, stream=None, **kwargs):
        if stream is None:
            stream = StringIO()
            dumper(documents, stream, **kwargs)
            return stream.getvalue()
        dumper(documents, stream)
    return wrapper


class Representer(ryaml.representer.RoundTripRepresenter):
    pass

Representer.add_representer(OrderedDict, Representer.represent_dict)
Representer.add_representer(ChangesDict, Representer.represent_dict)
Representer.add_representer(ChangesList, Representer.represent_list)


# Regular safe interface. No support for round-trip

safe_yaml = ryaml.YAML(typ='safe')
safe_yaml.indent(mapping=2, sequence=4, offset=2)

load = safe_yaml.load
load_all = safe_yaml.load_all
dump = _optional_stream(safe_yaml.dump)
dump_all = _optional_stream(safe_yaml.dump_all)


# Roud-trip interface

rt_yaml = ryaml.YAML(typ='rt')
rt_yaml.Representer = Representer
rt_yaml.indent(mapping=2, sequence=4, offset=2)

rt_load = rt_yaml.load
rt_load_all = rt_yaml.load_all
rt_dump = _optional_stream(rt_yaml.dump)
rt_dump_all = _optional_stream(rt_yaml.dump_all)


# Define generic map used by ruamel.yaml
Dict = rt_yaml.map
