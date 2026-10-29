"""Plain values the document model's interface hands around (W3-04): structs such as a
line spacing or a tab stop, and enumerations such as a font slant, as Python objects."""


class Struct:
    """A struct value: attributes it wasn't given read as 0."""

    def __init__(self, typename, **kw):
        self.__dict__["typeName"] = typename
        self.__dict__.update(kw)

    def __getattr__(self, k):
        if k.startswith("__"):
            raise AttributeError(k)
        return 0

    def __eq__(self, o):
        return isinstance(o, Struct) and o.__dict__ == self.__dict__

    def __repr__(self):
        return "<%s %r>" % (self.typeName, {k: v for k, v in self.__dict__.items() if k != "typeName"})


class Enum:
    def __init__(self, typename, value):
        self.typeName, self.value = typename, value

    def __eq__(self, o):
        return getattr(o, "value", o) == self.value and getattr(o, "typeName", self.typeName) == self.typeName

    def __hash__(self):
        return hash((self.typeName, self.value))

    def __repr__(self):
        return "<Enum %s.%s>" % (self.typeName, self.value)


def struct(name, **kw):
    return Struct(name, **kw)


def enum(typ, value):
    return Enum(typ, value)


def prop(name, value):
    return Struct("com.sun.star.beans.PropertyValue", Name=name, Value=value)
