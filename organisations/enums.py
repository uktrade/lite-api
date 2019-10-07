class OrganisationType:
    HMRC = 'hmrc'
    COMMERCIAL = 'commercial'
    INDIVIDUAL = 'individual'

    choices = [
        (HMRC, 'HMRC'),
        (COMMERCIAL, 'Commercial Organisation'),
        (INDIVIDUAL, 'Individual'),
    ]
