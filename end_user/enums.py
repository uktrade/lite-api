class EndUserType:
    GOVERNMENT = 'government'
    COMMERCIAL = 'commercial'
    INDIVIDUAL = 'individual'
    OTHER = 'other'

    choices = [
        (GOVERNMENT, 'Government'),
        (COMMERCIAL, 'Commercial Organisation'),
        (INDIVIDUAL, 'Individual'),
        (OTHER, 'Other'),
    ]
