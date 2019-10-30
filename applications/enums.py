class ApplicationExportType:
    PERMANENT = 'permanent'
    TEMPORARY = 'temporary'

    choices = [
        (PERMANENT, 'Permanent'),
        (TEMPORARY, 'Temporary'),
    ]


class ApplicationType:
    STANDARD_LICENCE = 'standard_licence'
    OPEN_LICENCE = 'open_licence'
    HMRC_QUERY = 'hmrc_query'

    choices = [
        (STANDARD_LICENCE, 'Standard licence'),
        (OPEN_LICENCE, 'Open licence'),
        (HMRC_QUERY, 'HMRC query'),
    ]


class ApplicationExportLicenceOfficialType:
    YES = 'yes'
    NO = 'no'

    choices = [
        (YES, 'Yes'),
        (NO, 'No'),
    ]
