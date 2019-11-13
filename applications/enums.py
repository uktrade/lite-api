class ApplicationExportType:
    PERMANENT = "permanent"
    TEMPORARY = "temporary"

    choices = [
        (PERMANENT, "Permanent"),
        (TEMPORARY, "Temporary"),
    ]


class ApplicationLicenceType:
    STANDARD_LICENCE = "standard_licence"
    OPEN_LICENCE = "open_licence"

    choices = [
        (STANDARD_LICENCE, "Standard Licence"),
        (OPEN_LICENCE, "Open Licence"),
    ]


class ApplicationExportLicenceOfficialType:
    YES = "yes"
    NO = "no"

    choices = [
        (YES, "Yes"),
        (NO, "No"),
    ]
