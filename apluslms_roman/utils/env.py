import re
from collections.abc import MutableMapping, Sequence

from json import dumps as to_json

from apluslms_yamlidator.utils import convert_to_boolean as to_bool
from apluslms_yamlidator.utils.collections import OrderedDict
from apluslms_yamlidator.utils.error_render import render_lc

from .translation import _


# simple variables with no substitutions, e.g. ${PATH}
var_rgx = r'\$\{[a-zA-Z_][a-zA-Z0-9_]*\}'
# if a var doesn't match the above regex but matches this one, it
# either has some sort of substitution syntax or is a variable
# with forbidden characters. e.g. ${PATH:-$HOME} (substitution)
# or ${Pat!h} (forbidden chars in name)
sub_rgx = r'\$\{[^}{]+\}'
quoted_rgx = r'(\"[^\"]*\")|(\'[^\']*\')'

# regexes for patterns like a/b
# left side can't be empty and neither can contain /, but
# if they're quoted / is okay
replacement_rgxs = (
    '[^/]+/[^/]*',
    '({0})/({0})'.format(quoted_rgx),
    '({})/[^/]*'.format(quoted_rgx),
    '[^/]+/({})'.format(quoted_rgx)
)


class EnvError(Exception):
    pass


def find_separator(pattern):
    separator = [s for s in SEPARATORS if s in pattern]
    if not separator:
        raise EnvError(_("Unrecognized parameter substitution pattern"))
    return min(separator, key=lambda s: pattern.index(s))


def to_str(data):
    if data is None or isinstance(data, str):
        return data
    if hasattr(data, 'get_data'):
        data = data.get_data()
    return to_json(data)


def default_value(var, default):
    return var if var is not None else default


def alt_value(var, alternative):
    return alternative if var is not None else ""


def replace_once(var, pattern):
    return replace(var, pattern, 1)


def replace_all(var, pattern):
    return replace(var, pattern, 0)


def replace(var, pattern, count):
    var = to_str(var)
    try:
        regex, replacement = parse_replacement_pattern(pattern)
    except ValueError:
        sep = '/' if count else '//'
        raise EnvError(_(
            "Wrong pattern replacement syntax. The format "
            "should be ${{var{}pattern/replacement}}. ").format(sep))
    return re.sub(regex, replacement, var, count=count)


# separators currently recognized by the script
SEPARATORS = OrderedDict((
    (":-", {'func': default_value, 'allow_missing': True}),
    (":+", {'func': alt_value, 'allow_missing': True}),
    ("//", {'func': replace_all, 'allow_missing': False}),
    ("/", {'func': replace_once, 'allow_missing': False}),
))


def parse_replacement_pattern(pattern):
    matches = [rgx for rgx in replacement_rgxs if re.fullmatch(rgx, pattern)]
    if not matches:
        raise ValueError

    # no extra '/'
    if replacement_rgxs[0] in matches:
        regex, replacement = pattern.split("/")
    # both parts are quoted
    elif replacement_rgxs[1] in matches:
        # the 'quoted' regex returns a tuple as a match object because
        # there are two options ('' or  "")
        regex, replacement = re.findall(quoted_rgx, pattern)
        regex = regex[0] or regex[1]
        replacement = replacement[0] or replacement[1]
    # first part is quoted
    elif replacement_rgxs[2] in matches:
        regex = re.search(quoted_rgx, pattern).group(0)
        replacement = pattern.rpartition('/')[2]
    # second part is quoted
    else:
        replacement = re.search(quoted_rgx, pattern).group(0)
        regex = pattern.partition('/')[0]

    regex = regex.strip('\'"')
    replacement = replacement.strip('\'"')

    return regex, replacement


def update(env, key, value):
    if isinstance(value, str):
        value = get_val(env, key, value)
    elif isinstance(value, (list, Sequence)):
        for i, item in enumerate(value):
            value[i] = get_val(env, key, item)
    elif isinstance(value, (dict, MutableMapping)):
        for key_, item in value.items():
            value[key_] = get_val(env, key, item)

    env[key] = value


def get_val(env, key, value):
    references_self = _("Variable {} references itself")
    not_defined = _("{} hasn't been defined")

    if isinstance(value, int):
        return value
    value = to_str(value)
    while True:
        var = re.search(sub_rgx, value)
        if not var:
            break
        var = var.group(0)
        if not re.fullmatch(var_rgx, var):
            # ${var} -> var
            content = var[2:-1]
            sep = find_separator(content)

            parts = content.partition(sep)[::2]
            val = env.get(parts[0], None)
            if val is None and not SEPARATORS[sep]['allow_missing']:
                if key == parts[0]:
                    raise EnvError(references_self.format(key))
                raise EnvError(not_defined.format(parts[0]))
            val = SEPARATORS[sep]['func'](val, parts[1])
            if value == var:
                return val
            value = value.replace(var, val)
        else:
            val = var[2:-1]
            if val not in env:
                if val == key:
                    raise EnvError(references_self.format(key))
                raise EnvError(not_defined.format(val))
            val = env[val]
            if value == var:
                return val
            val = to_str(val)
            value = value.replace(var, val)

    return value


class EnvDict(OrderedDict):

    def __init__(self, *args):
        self.envs = OrderedDict()
        for env in args:
            self.add_env(*env)
        super().__init__()

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, super().__str__())

    def add_env(self, environment, name):
        self.envs[name] = environment or []

    def get_env(self, name):
        return self.envs[name]

    def find_in_env(self, name, key):
        return [item for item in self.envs[name]
            if (isinstance(item, MutableMapping) and (key in item
                or ('name' in item and item['name'] == key)))
            or (isinstance(item, str) and key == item.split('=')[0])]

    def set_in_env(self, name, key, val):
        env = self.envs[name]
        item = '{}={}'.format(key, val)
        matches = self.find_in_env(name, key)
        if not matches:
            env.append(item)
        else:
            first = env.index(matches[0])
            env[first] = item
            if len(matches) > 1:
                env = (env[:first + 1]
                    + [item for item in env[first + 1:] if key not in item])

        self.envs[name] = env

    def delete_from_env(self, name, key, delete_unset=False):
        if key.isdigit():
            self.envs[name].pop(int(key))
        else:
            to_delete = self.find_in_env(name, key)
            if not delete_unset:
                to_delete = [item for item in to_delete if 'unset' not in item]
            if not to_delete:
                return False
            self.envs[name] = [item for item in self.envs[name]
                if item not in to_delete]
            return True

    def add_to_env(self, name, val):
        self.envs[name].append(val)

    def get_combined(self):
        combined = OrderedDict()

        def expand_env(item, env_name, env_idx):
            if 'name' in item:
                if 'unset' in item:
                    if to_bool(item['unset']) and item['name'] in combined:
                        del combined[item['name']]
                        return
                else:
                    item = {item['name']: item['value']}
            for key in item:
                try:
                    update(combined, key, item[key])
                except EnvError as err:
                    self._raise_err(str(err), env_idx, env_name)

        for name, env in self.envs.items():
            for idx, item in enumerate(env):
                if isinstance(item, str):
                    key, _, val = item.partition('=')
                    item = {key: val}
                expand_env(item, name, idx)
        return combined

    # env_idx is used when env is a list
    def _raise_err(self, message, idx, env_name):
        env = self.envs[env_name]
        if hasattr(env, 'get_root'):
            source_file = env.get_root().path
            file_info = "{} ({})".format(env_name, source_file)

            num_lines = 5
            item = env[idx]
            if not isinstance(item, str):
                val = list(item.items())[0][1]
                if not isinstance(val, str):
                    num_lines = -len(val)
            line, col = env.get_data().lc.item(idx)

            lines = render_lc(source_file, line, col,
                num_lines=num_lines, print_file=False)
            lines = "\n".join(lines).replace("^", "^ {}".format(message))

            raise EnvError(_("Invalid environment variable at index {} in {}:\n{}")
                .format(idx, file_info, lines))
        raise EnvError(_("Invalid environment variable at index {}: {}")
            .format(env[idx], message))
