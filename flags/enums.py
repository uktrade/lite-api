class FlagLevels:
    CASE = 'Case'
    ORGANISATION = 'Organisation'
    GOOD = 'Good'
    DESTINATION = 'Destination'

    choices = [
        (CASE, 'Case'),
        (ORGANISATION, 'Organisation'),
        (GOOD, 'Good'),
        (DESTINATION, 'Destination'),
    ]


class FlagStatuses:
    ACTIVE = 'Active'
    DEACTIVATED = 'Deactivated'

    choices = [
        (ACTIVE, 'Active'),
        (DEACTIVATED, 'Deactivated'),
    ]


class SystemFlags:
    REFUSAL_FLAG = 'refusal_advice'

    flags = [
        (REFUSAL_FLAG, 'Refusal Advice')
    ]

    id = {
        REFUSAL_FLAG: '00000000-0000-0000-0000-000000000001'
    }



