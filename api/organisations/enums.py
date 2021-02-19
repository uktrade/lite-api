class OrganisationType:
    HMRC = "hmrc"
    COMMERCIAL = "commercial"
    INDIVIDUAL = "individual"

    choices = [
        (HMRC, "HMRC"),
        (COMMERCIAL, "Commercial Organisation"),
        (INDIVIDUAL, "Individual"),
    ]

    @classmethod
    def as_list(cls):
        return [choice[0] for choice in cls.choices]


class OrganisationDocumentType:
    FIREARM_SECTION_ONE = "section-one-certificate"
    FIREARM_SECTION_TWO = "section-two-certificate"
    FIREARM_SECTION_FIVE = "section-five-certificate"
    REGISTERED_FIREARM_DEALER_CERTIFICATE = "rfd-certificate"

    choices = [
        (FIREARM_SECTION_ONE, "Firearm Section 1 certificate"),
        (FIREARM_SECTION_TWO, "Firearm Section 2 certificate"),
        (FIREARM_SECTION_FIVE, "Firearm Section 5 certificate"),
        (REGISTERED_FIREARM_DEALER_CERTIFICATE, "Registered Firearm Dealer certificate"),
    ]


class OrganisationStatus:
    ACTIVE = "active"
    IN_REVIEW = "in_review"
    REJECTED = "rejected"

    choices = [
        (ACTIVE, "Active"),
        (IN_REVIEW, "In review"),
        (REJECTED, "Rejected"),
    ]


class LocationType:
    LAND_BASED = "land_based"
    SEA_BASED = "sea_based"

    choices = [
        (LAND_BASED, "Land based"),
        (SEA_BASED, "Vessel (sea) based"),
    ]
