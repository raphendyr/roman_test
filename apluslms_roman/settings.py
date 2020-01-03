from abc import abstractmethod
from os.path import join

from apluslms_yamlidator.document import Document
from apluslms_yamlidator.utils.collections import OrderedDefaultDict, OrderedDict
from apluslms_yamlidator.utils.version import Version

from . import CONFIG_DIR
from .utils.translation import _


METAVARS = {
    'integer': _('INT'),
    'boolean': None,
}


class Undefined:
    pass


class Settings(Document):
    @property
    @abstractmethod
    def name(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def schema(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def version(self):
        raise NotImplementedError

    @classmethod
    def get_config_path(cls, filename=None):
        if filename is None:
            filename = cls.name + '.yml'
        return join(CONFIG_DIR, filename)

    @classmethod
    def load(cls, path, allow_missing=False):
        return super().load(path, version=cls.version, allow_missing=allow_missing)


class ArgumentSettingsMeta(type(Settings)):

    def __init__(cls, name, bases, namespace, **kwargs):
        super().__init__(name, bases, namespace, **kwargs)

        groups = OrderedDict()
        if hasattr(cls, '_ARGUMENT_GROUPS'):
            groups.update(cls._ARGUMENT_GROUPS)
        for name, title, desc in cls.ARGUMENT_GROUPS:
            groups[name] = (title, desc)
        cls._ARGUMENT_GROUPS = groups

        args = OrderedDefaultDict(list)
        if hasattr(cls, '_ARGUMENTS'):
            for k, v in cls._ARGUMENTS.items():
                args[k] = list(v)
        for option, *opts in cls.ARGUMENTS:
            group, meta, name, *__ = opts + [None, None, None]
            if name is None:
                name = option.replace('.', '-').replace('_', '-')
            args[group].append((option, name, meta))
        cls._ARGUMENTS = args


class ArgumentSettings(Settings, metaclass=ArgumentSettingsMeta):
    ARGUMENT_GROUPS = ()
    ARGUMENTS = ()

    @classmethod
    def populate_parser(cls, parser):
        # ArgumentSettings requires a valid schema to contain rest of the options
        validator = cls.Container.get_validator(cls.version)
        if not validator:
            raise TypeError(("{0}.Container.get_validator() failed. Is {0}.schema defined?"
                ).format(cls.__name__))
        for gname, (gtitle, gdesc) in cls._ARGUMENT_GROUPS.items():
            group = parser.add_argument_group(gtitle, description=gdesc) if gtitle else parser
            for option, name, meta in cls._ARGUMENTS.get(gname, ()):
                # TODO: implement validator to resolve $ref and other elements
                fragment = '/'.join('properties/' + part for part in option.split('.'))
                try:
                    schema = validator.resolver.resolve_fragment(validator.schema, fragment)
                except Exception:
                    schema = {}
                title = schema.get('title', name)
                desc = schema.get('description', title)
                type_ = schema.get('type', 'string')
                if meta is None:
                    meta = METAVARS.get(type_, _(type_.upper()))
                if type_ == 'boolean':
                    default = schema.get('default', False)
                    action = 'store_false' if default else 'store_true'
                    group.add_argument('--'+name, action=action, default=Undefined, help=_(desc))
                else:
                    group.add_argument('--'+name, metavar=meta, default=Undefined, help=_(desc))

    def update_from_namespace(self, namespace, store=False):
        set_ = self.mlset if store else self.mlsetwork
        for arguments in self._ARGUMENTS.values():
            for option, name, _ in arguments:
                value = getattr(namespace, name.replace('-', '_'), Undefined)
                if value is not Undefined:
                    # FIXME: validate the value
                    set_(option, value)


class GlobalSettings(ArgumentSettings):
    name = 'roman_settings'
    schema = name
    version = Version(1, 0)

    ARGUMENT_GROUPS = (
        # name, title, description
        ('backend', _("Backend"), _("Backend driver configuration")),
    )

    ARGUMENTS = (
        # option, group name, meta war, argument name
        ('backend', 'backend', _('MODULE')),
        ('docker.host', 'backend', _('URL')),
        ('docker.timeout', 'backend'),
    )
