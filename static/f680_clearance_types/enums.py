from uuid import UUID


class F680ClearanceTypeEnum:
    MARKET_SURVEY = "market_survey"
    INITIAL_DISCUSSIONS_AND_PROMOTIONS = "initial_discussions_and_promotions"
    DEMONSTRATION_IN_THE_UK_TO_OVERSEAS_CUSTOMERS = "demonstration_uk_overseas_customers"
    DEMONSTRATION_OVERSEAS = "demonstration_overseas"
    TRAINING = "training"
    THROUGH_LIFE_SUPPORT = "through_life_support"

    choices = [
        (MARKET_SURVEY, "Market Survey"),
        (INITIAL_DISCUSSIONS_AND_PROMOTIONS, "Initial discussions and promotions"),
        (DEMONSTRATION_IN_THE_UK_TO_OVERSEAS_CUSTOMERS, "Demonstration in the UK to overseas customers"),
        (DEMONSTRATION_OVERSEAS, "Demonstration overseas"),
        (TRAINING, "Training"),
        (THROUGH_LIFE_SUPPORT, "Through life support"),
    ]

    ids = {
        MARKET_SURVEY: UUID("00000000-0000-0000-0000-000000000001"),
        INITIAL_DISCUSSIONS_AND_PROMOTIONS: UUID("00000000-0000-0000-0000-000000000002"),
        DEMONSTRATION_IN_THE_UK_TO_OVERSEAS_CUSTOMERS: UUID("00000000-0000-0000-0000-000000000003"),
        DEMONSTRATION_OVERSEAS: UUID("00000000-0000-0000-0000-000000000004"),
        TRAINING: UUID("00000000-0000-0000-0000-000000000005"),
        THROUGH_LIFE_SUPPORT: UUID("00000000-0000-0000-0000-000000000006"),
    }

    @classmethod
    def get_text(cls, status):
        for k, v in cls.choices:
            if status == k:
                return v
