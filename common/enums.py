from enum import EnumMeta, Enum, _EnumDict


class autostr:
    """
    Enum value class for auto assigning enum values to lowercase key string
    """


class StrValueEnumMeta(EnumMeta):
    def __new__(metacls, cls, bases, oldclassdict):
        """
        Override class dict to replace enum `autostr` value with lowercase key.
        """
        newclassdict = _EnumDict()
        for k, v in oldclassdict.items():
            if isinstance(v, autostr):
                v = k.lower()
            newclassdict[k] = v
        return super().__new__(metacls, cls, bases, newclassdict)


class LiteEnum(str, Enum, metaclass=StrValueEnumMeta):
    """
    Custom Enum that allows str comparisons without calling value.

    class NormalEnum(Enum):
        KEY = "key"

    NormalEnum.KEY != "key"
    NormalEnum.KEY.value == "key"


    class CustomEnum(LiteEnum):
        KEY = "KEY"
        KEY_2 = autostr()

    CustomEnum.KEY == "KEY"
    CustomEnum.KEY.value == "KEY"
    CustomEnum.KEY_2 == "key_2"
    CustomEnum.KEY_2.value == "key_2"
    """


class SortOrder(LiteEnum):
    ASCENDING = autostr()
    DESCENDING = autostr()
