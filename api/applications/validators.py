from api.applications.enums import ApplicationExportType
from api.cases.enums import CaseTypeSubTypeEnum
from api.parties.models import PartyDocument
from api.parties.enums import PartyType, PartyDocumentType

from lite_content.lite_api import strings


def siel_end_user_validator(application):
    error = None
    if not application.end_user:
        error = "To submit the application, add an end user"

    party = application.end_user.party
    breakpoint()
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

    return {"end_user": [error]} if error else None


class BaseApplicationValidator:
    config = {}

    def __init__(self, application):
        self.application = application

    def validate(self):
        all_errors = {}
        for _, func in self.config.items():
            errors = func(self.application)
            all_errors = {**errors, **all_errors}

        return all_errors


class StandardApplicationValidator(BaseApplicationValidator):
    config = {
        "end_user": siel_end_user_validator,
        # more to follow
    }
