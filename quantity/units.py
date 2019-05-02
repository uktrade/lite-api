from enumchoicefield import ChoiceEnum, EnumChoiceField
from collections import namedtuple


class Units(ChoiceEnum):
    GRM = "Gram"
    KGM = "Kilogram"
    NAR = "Number of articles"
    MTK = "Square metre"
    MTR = "Metre"
    LTR = "Litre"
    MTQ = "Cubic metres"

