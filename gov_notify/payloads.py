from dataclasses import dataclass, fields


@dataclass(frozen=True)
class EmailData:
    """
    Base class for email payloads.
    """

    def as_dict(self):
        return {field.name: getattr(self, field.name) for field in fields(self)}


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
class ExporterLicenceRefused(EmailData):
    user_first_name: str
    application_reference: str
    exporter_frontend_url: str


@dataclass(frozen=True)
class ExporterF680OutcomeIssued(EmailData):
    user_first_name: str
    application_reference: str
    exporter_frontend_url: str


@dataclass(frozen=True)
class ExporterLicenceRevoked(EmailData):
    user_first_name: str
    application_reference: str


@dataclass(frozen=True)
class ExporterLicenceSuspended(EmailData):
    user_first_name: str
    licence_reference: str


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
class ExporterECJUQueryChaser(EmailData):
    case_reference: str
    exporter_frontend_ecju_queries_url: str
    remaining_days: int
    open_working_days: int
    exporter_first_name: str


@dataclass(frozen=True)
class CaseWorkerNewRegistration(EmailData):
    organisation_name: str
    applicant_email: str


@dataclass(frozen=True)
class ExporterCaseOpenedForEditing(EmailData):
    user_first_name: str
    application_reference: str
    exporter_frontend_url: str


@dataclass(frozen=True)
class ExporterNoLicenceRequired(EmailData):
    user_first_name: str
    application_reference: str
    exporter_frontend_url: str


@dataclass(frozen=True)
class ExporterInformLetter(EmailData):
    user_first_name: str
    application_reference: str
    exporter_frontend_url: str


@dataclass(frozen=True)
class ExporterAppealAcknowledgement(EmailData):
    user_first_name: str
    application_reference: str


@dataclass(frozen=True)
class CaseWorkerCountersignCaseReturn(EmailData):
    case_reference: str
    countersigned_user_name: str
    countersign_reasons: str
    recommendation_section_url: str
