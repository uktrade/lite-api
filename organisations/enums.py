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
