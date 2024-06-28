class Units:
    GRM = "GRM"
    KGM = "KGM"
    NAR = "NAR"
    MTK = "MTK"
    MTR = "MTR"
    LTR = "LTR"
    MTQ = "MTQ"
    TON = "TON"
    MGM = "MGM"
    MCG = "MCG"
    MLT = "MLT"
    MCL = "MCL"

    choices = [
        (NAR, "Items"),
        (TON, "Tonnes"),
        (KGM, "Kilograms"),
        (GRM, "Grams"),
        (MGM, "Milligrams"),
        (MCG, "Micrograms"),
        (MTR, "Metres"),
        (MTK, "Square metres"),
        (MTQ, "Cubic metres"),
        (LTR, "Litres"),
        (MLT, "Millilitres"),
        (MCL, "Microlitres"),
    ]

    @classmethod
    def to_str(cls, obj):
        return next(choice[1] for choice in cls.choices if choice[0] == obj)
