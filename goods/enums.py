class GoodStatus:
    DRAFT = 'draft'
    SUBMITTED = 'submitted'
    CLC_QUERY = 'clcquery'
    FINAL = 'final'

    choices = [
        (DRAFT, 'Draft'),
        (SUBMITTED, 'Submitted'),
        (CLC_QUERY, 'Control List Classification Query'),
        (FINAL, 'Final')
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


class GoodAreYouSure:
    YES = 'yes'
    NO = 'no'

    choices = [
        (YES, 'Yes'),
        (NO, 'No')
    ]