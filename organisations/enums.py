class OrganisationType:
    HMRC = "hmrc"
    COMMERCIAL = "commercial"
    INDIVIDUAL = "individual"

    choices = [
        (HMRC, "HMRC"),
        (COMMERCIAL, "Commercial Organisation"),
        (INDIVIDUAL, "Individual"),
    ]


class OrganisationStatus:
    ACTIVE = "active"
    IN_REVIEW = "in_review"

    choices = [
        (ACTIVE, "Active"),
        (IN_REVIEW, "In review"),
    ]
