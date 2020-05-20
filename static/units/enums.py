class Units:
    """
    LITE Frontend can dynamically pluralise these
    units, to enable this include an (s) at the
    end of the unit.
    """

    GRM = "GRM"
    KGM = "KGM"
    NAR = "NAR"
    MTK = "MTK"
    MTR = "MTR"
    LTR = "LTR"
    MTQ = "MTQ"
    ITG = "ITG"

    choices = [
        (GRM, "Gram(s)"),
        (KGM, "Kilogram(s)"),
        (NAR, "Number of articles"),
        (MTK, "Square metre(s)"),
        (MTR, "Metre(s)"),
        (LTR, "Litre(s)"),
        (MTQ, "Cubic metre(s)"),
        (ITG, "Intangible"),
    ]

    choices_as_dict = {key: value for key, value in choices}
