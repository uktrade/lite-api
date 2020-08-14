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
