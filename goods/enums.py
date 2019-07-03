class GoodStatus:
    DRAFT = 'draft'
    SUBMITTED = 'submitted'
    CLCQUERY = 'clcquery'

    choices = [
        (DRAFT, 'draft'),
        (SUBMITTED, 'submitted'),
        (CLCQUERY, 'clcquery')
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
