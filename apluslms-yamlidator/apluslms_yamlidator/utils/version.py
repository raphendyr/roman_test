from collections import namedtuple

Version = namedtuple('Version', ('major', 'minor'))
Version.__new__.__defaults__ = (1, 0)
class Version(Version):
    def __str__(self):
        return "%d.%d" % self

def parse_version(version):
    if isinstance(version, Version):
        return version
    if isinstance(version, tuple):
        return Version(*version[:2])

    parts = []
    for x in str(version).split('.'):
        try:
            parts.append(int(x))
        except ValueError:
            break
    if not parts:
        raise ValueError(repr(version))
    return Version(*parts[:2])
