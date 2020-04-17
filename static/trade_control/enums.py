class TradeControlActivity:
    TRANSFER_OF_GOODS = "transfer_of_goods"
    PROVISION_OF_TRANSPORTATION = "provision_of_transportation"
    PROVISION_OF_FINANCE = "provision_of_finance"
    PROVISION_OF_INSURANCE = "provision_of_insurance"
    PROVISION_OF_ADVERTISING = "provision_of_advertising"
    MARITIME_ANTI_PIRACY = "maritime_anti_piracy"
    OTHER = "other"

    choices = [
        (TRANSFER_OF_GOODS, "Transfer of goods"),
        (PROVISION_OF_TRANSPORTATION, "Transportation services"),
        (PROVISION_OF_FINANCE, "Finance or financial services"),
        (PROVISION_OF_INSURANCE, "Insurance or reinsurance"),
        (PROVISION_OF_ADVERTISING, "General advertising or promotion services"),
        (MARITIME_ANTI_PIRACY, "Maritime anti-piracy"),
        (OTHER, "Other"),
    ]

    @classmethod
    def get_text(cls, choice):
        for key, value in cls.choices:
            if key == choice:
                return value


class TradeControlProductCategory:
    CATEGORY_A = "category_a"
    CATEGORY_B = "category_b"
    CATEGORY_C = "category_c"

    choices = [
        (CATEGORY_A, "Category A"),
        (CATEGORY_B, "Category B"),
        (CATEGORY_C, "Category C"),
    ]

    @classmethod
    def get_text(cls, choice):
        for key, value in cls.choices:
            if key == choice:
                return value
