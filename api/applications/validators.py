from api.applications.enums import ApplicationExportType
from api.cases.enums import CaseTypeSubTypeEnum
from api.parties.models import PartyDocument
from api.parties.enums import PartyType, PartyDocumentType

from lite_content.lite_api import strings


def siel_locations_validator(application):
    from api.applications.models import SiteOnApplication

    error = None

    export_type_choices = [item[0] for item in ApplicationExportType.choices]
    starting_point_choices = [item[0] for item in application.GOODS_STARTING_POINT_CHOICES]
    recipient_choices = [item[0] for item in application.GOODS_RECIPIENTS_CHOICES]

    if not (
        SiteOnApplication.objects.filter(application=application).exists()
        and application.export_type in export_type_choices
        and application.goods_starting_point in starting_point_choices
        and application.goods_recipients in recipient_choices
        and application.is_shipped_waybill_or_lading is not None
    ):
        error = "To submit the application, add a product location"

    return error


def siel_end_user_validator(application):
    error = None
    if not application.end_user:
        error = "To submit the application, add an end user"

    party = application.end_user.party
    documents_qs = PartyDocument.objects.filter(
        party=party, type=PartyDocumentType.END_USER_UNDERTAKING_DOCUMENT
    ).values_list("safe", flat=True)
    if documents_qs.exists():
        if None in documents_qs:
            error = "We're still processing the end user document. Please submit again"
        elif False in documents_qs:
            error = "To submit the application, attach a document that does not contain a virus to the end user"
    else:
        if not party.end_user_document_available and not party.end_user_document_missing_reason:
            error = "To submit the application, attach a document to the end user"

    return error


def siel_security_approvals_validator(application):
    error = "To submit the application, complete the 'Do you have a security approval?' section"

    return error if application.is_mod_security_approved is None else None


class BaseApplicationValidator:
    config = {}

    def __init__(self, application):
        self.application = application

    def validate(self):
        all_errors = {}
        for entity, func in self.config.items():
            error = func(self.application)
            if error:
                entity_errors = {entity: [error]}
                all_errors = {**entity_errors, **all_errors}

        return all_errors


class StandardApplicationValidator(BaseApplicationValidator):
    config = {
        "location": siel_locations_validator,
        "end_user": siel_end_user_validator,
        "security_approvals": siel_security_approvals_validator,
    }
