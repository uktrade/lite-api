class CaseType:
    APPLICATION = 'application'
    CLC_QUERY = 'clc_query'

    choices = [
        (APPLICATION, 'Application'),
        (CLC_QUERY, 'CLC Query'),
    ]


class AdviceType:
    APPROVE = 'approve'
    PROVISO = 'proviso'
    REFUSE = 'refuse'
    NO_LICENCE_REQUIRED = 'no_licence_required'
    NOT_APPLICABLE = 'not_applicable'

    choices = [
        (APPROVE, 'Approve'),
        (PROVISO, 'Proviso'),
        (REFUSE, 'Refuse'),
        (NO_LICENCE_REQUIRED, 'No Licence Required'),
        (NOT_APPLICABLE, 'Not Applicable'),
    ]
