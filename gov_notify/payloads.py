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


@dataclass(frozen=True)
class ExporterECJUQuery(EmailData):
    case_reference: str
    exporter_first_name: str
    exporter_frontend_url: str


@dataclass(frozen=True)
class CaseWorkerNewRegistration(EmailData):
    organisation_name: str
    applicant_email: str


@dataclass(frozen=True)
class ExporterCaseOpenedForEditing(EmailData):
    user_first_name: str
    application_reference: str
    exporter_frontend_url: str
