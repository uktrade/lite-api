class Units:
    GRM = "GRM"
    KGM = "KGM"
    NAR = "NAR"
    MTK = "MTK"
    MTR = "MTR"
    LTR = "LTR"
    MTQ = "MTQ"
    TON = "TON"
    MIM = "MIM"
    MCM = "MCM"
    MIR = "MIR"
    MCR = "MCR"

    choices = [
        (NAR, "Items"),
        (TON, "Tonnes"),
        (KGM, "Kilograms"),
        (GRM, "Grams"),
        (MIM, "Milligrams"),
        (MCM, "Micrograms"),
        (MTR, "Metres"),
        (MTK, "Square metres"),
        (MTQ, "Cubic metres"),
        (LTR, "Litres"),
        (MIR, "Millilitres"),
        (MCR, "Microlitres"),
    ]

    @classmethod
    def to_str(cls, obj):
        return next(choice[1] for choice in cls.choices if choice[0] == obj)
