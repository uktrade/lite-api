from api.applications.models import ApplicationDocument
from api.core.helpers import str_to_bool
from lite_content.lite_api import strings


def _get_document_errors(documents, processing_error, virus_error):
    document_statuses = documents.values_list("safe", flat=True)

    # If safe is None, then the document hasn't been virus scanned yet
    if not all([safe is not None for safe in document_statuses]):
        return processing_error

    # If safe is False, the file contains a virus
    if not all(document_statuses):
        return virus_error


def _validate_agree_to_declaration(request, errors):
    """Checks the exporter has agreed to the T&Cs of the licence"""

    if "agreed_to_foi" in request.data and str_to_bool(request.data["agreed_to_foi"]):
        if "foi_reason" not in request.data or request.data["foi_reason"] == "":
            errors["foi_reason"] = [
                "To submit the application, you must answer why the disclosure of information would be harmful to your interests"
            ]

    text = request.data.get("agreed_to_declaration_text", "").lower()
    if text != "i agree":
        errors["agreed_to_declaration_text"] = [
            "To submit the application, you must confirm that you agree by typing “I AGREE”"
        ]

    return errors


def _validate_additional_documents(draft, errors):
    """Validate additional documents"""
    documents = ApplicationDocument.objects.filter(application=draft)

    if documents:
        document_errors = _get_document_errors(
            documents,
            processing_error=strings.Applications.Standard.ADDITIONAL_DOCUMENTS_PROCESSING,
            virus_error=strings.Applications.Standard.ADDITIONAL_DOCUMENTS_INFECTED,
        )

        if document_errors:
            errors["supporting-documents"] = [document_errors]

    return errors


def validate_application_ready_for_submission(application):
    errors = {}

    errors = application.validate()
    errors = _validate_additional_documents(application, errors)

    return errors
