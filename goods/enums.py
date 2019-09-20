class GoodStatus:
    DRAFT = 'draft'  # Freshly created good, fully editable
    SUBMITTED = 'submitted'  # This good is on use in an application
    CLC_QUERY = 'clc_query'  # This good is in a CLC Query
    VERIFIED = 'verified'  # This good's details have been verified to be correct

    choices = [
        (DRAFT, 'Draft'),
        (SUBMITTED, 'Submitted'),
        (CLC_QUERY, 'Control List Classification Query'),
        (VERIFIED, 'Verified')
    ]


class GoodControlled:
    YES = 'yes'
    NO = 'no'
    UNSURE = 'unsure'

    choices = [
        (YES, 'Yes'),
        (NO, 'No'),
        (UNSURE, 'I don\'t know')
    ]
