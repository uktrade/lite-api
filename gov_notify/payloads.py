from dataclasses import dataclass, fields


@dataclass(frozen=True)
class EmailData:
    """
    Base class for email payloads.
    """

    def as_dict(self):
        return {field.name: getattr(self, field.name) for field in fields(self)}


@dataclass(frozen=True)
class EcjuCreatedEmailData(EmailData):
    case_reference: str
    application_reference: str
    link: str


@dataclass(frozen=True)
class EcjuComplianceCreatedEmailData(EmailData):
    query: str
    case_reference: str
    site_name: str
    site_address: str
    link: str


@dataclass(frozen=True)
class ApplicationStatusEmailData(EmailData):
    case_reference: str
    application_reference: str
    link: str


@dataclass(frozen=True)
class ExporterRegistration(EmailData):
    organisation_name: str


@dataclass(frozen=True)
class ExporterUserAdded(EmailData):
    organisation_name: str
    exporter_frontend_url: str


@dataclass(frozen=True)
class ExporterLicenceIssued(EmailData):
    user_first_name: str
    application_reference: str
    exporter_frontend_url: str


@dataclass(frozen=True)
class ExporterOrganisationApproved(EmailData):
    exporter_first_name: str
    organisation_name: str
    exporter_frontend_url: str


@dataclass(frozen=True)
class ExporterOrganisationRejected(EmailData):
    exporter_first_name: str
    organisation_name: str
