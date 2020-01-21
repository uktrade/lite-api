from applications.enums import ApplicationType, ApplicationExportType, DefaultDuration
from static.countries.models import Country


def get_default_duration(application):
    """
    Returns default duration in months

    Rules defined in: https://uktrade.atlassian.net/browse/LT-1586
    """

    if application.export_type == ApplicationExportType.TEMPORARY:
        return DefaultDuration.TEMPORARY.value

    elif (
        application.application_type == ApplicationType.STANDARD_LICENCE
        and application.export_type == ApplicationExportType.PERMANENT
    ):
        return DefaultDuration.PERMANENT_STANDARD.value

    elif (
        application.application_type == ApplicationType.OPEN_LICENCE
        and application.export_type == ApplicationExportType.PERMANENT
    ):
        is_eu = Country.objects.filter(countries_on_application__application=application, is_eu=True).exists()
        return DefaultDuration.PERMANENT_OPEN_EU.value if is_eu else DefaultDuration.PERMANENT_OPEN.value
