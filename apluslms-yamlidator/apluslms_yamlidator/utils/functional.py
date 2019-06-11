
class attrproxy:
    """
    Redirects/proxies get/set/del actions to a different attribute.
    """
    __slots__ = ('base', 'name')

    def __init__(self, *attr):
        if len(attr) == 1 and isinstance(attr[0], str):
            attr = attr[0].split('.')
        self.base = attr[:-1]
        self.name = attr[-1]

    def _resolve(self, obj):
        for a in self.base:
            obj = getattr(obj, a)
        return obj

    def __get__(self, obj, owner=None):
        return getattr(self._resolve(obj), self.name)

    def __set__(self, obj, value):
        setattr(self._resolve(obj), self.name, value)

    def __delete__(self, obj):
        delattr(self._resolve(obj), self.name)

# an alternative solution:
#from operator import attrgetter
#def attrproxy(attr):
#    get_ = attrgetter(attr)
#    attr, _, name = attr.rpartition('.')
#    getbase = attrgetter(attr) if attr else lambda o: o
#    def set_(obj, value):
#        setattr(getbase(obj), name, value)
#    def del_(obj):
#        delattr(getbase(obj), name)
#    return property(get_, set_, del_)
