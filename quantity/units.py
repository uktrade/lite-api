from enumchoicefield import ChoiceEnum, EnumChoiceField
from collections import namedtuple

Unit = namedtuple('Unit', ['acronym', 'label'])

# Gram(GRM)
    # Kilogram(KGM)
    # Number
    # of
    # articles(NAR)
    # Square
    # metre(MTK)
    # Metre(MTR)
    # Litre(LTR)
    # Cubic
    # metres(MTQ)


class Units(ChoiceEnum):
    KGM = "Kilogram"
    NAR = "Number of articles"
    # KGM = ('KGM', 'Kilogram')
    # NAR = ('NAR', 'Number of articles')
