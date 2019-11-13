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
    # If this is updated please check the seeding script to ensure that it still makes sense for current flags.
    REFUSAL_FLAG = 'refusal_advice'

    flags = [
        (REFUSAL_FLAG, 'Refusal Advice')
    ]

    id = {
        REFUSAL_FLAG: '00000000-0000-0000-0000-000000000001'
    }



