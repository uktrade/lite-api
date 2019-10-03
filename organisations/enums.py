class OrganisationType:
    HMRC = 'hmrc'
    COMMERCIAL = 'commercial'
    INDIVIDUAL = 'individual'

    choices = [
        (HMRC, 'Hmrc'),
        (COMMERCIAL, 'Commercial Organisation'),
        (INDIVIDUAL, 'Individual'),
    ]
