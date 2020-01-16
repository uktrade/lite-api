class ApplicationExportType:
    PERMANENT = "permanent"
    TEMPORARY = "temporary"

    choices = [
        (PERMANENT, "Permanent"),
        (TEMPORARY, "Temporary"),
    ]


class ApplicationType:
    STANDARD_LICENCE = "standard_licence"
    OPEN_LICENCE = "open_licence"
    HMRC_QUERY = "hmrc_query"

    choices = [
        (STANDARD_LICENCE, "Standard Licence"),
        (OPEN_LICENCE, "Open Licence"),
        (HMRC_QUERY, "HMRC Query"),
    ]


class ApplicationExportLicenceOfficialType:
    YES = "yes"
    NO = "no"

    choices = [
        (YES, "Yes"),
        (NO, "No"),
    ]


class Duration:
    MIN = 1
    MAX = 999
