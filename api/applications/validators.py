from django.db.models import Q

from api.applications.enums import ApplicationExportType
from api.goods.models import GoodDocument
from api.parties.models import PartyDocument
from api.parties.enums import PartyDocumentType


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


def siel_consignee_validator(application):
    from api.applications.models import StandardApplication

    error = None
    if application.goods_recipients not in [
        StandardApplication.VIA_CONSIGNEE,
        StandardApplication.VIA_CONSIGNEE_AND_THIRD_PARTIES,
    ]:
        return error

    if not application.consignee:
        return "To submit the application, add a consignee"

    party = application.consignee.party
    documents_qs = PartyDocument.objects.filter(party=party).values_list("safe", flat=True)
    if documents_qs.exists():
        if None in documents_qs:
            error = "We're still processing the consignee document. Please submit again"
        elif False in documents_qs:
            error = "To submit the application, attach a document that does not contain a virus to the end user"

    return error


def siel_third_parties_validator(application):
    """If there are third parties and they added any documents check if they are all valid"""
    error = None

    if application.third_parties.count() == 0:
        return error

    for third_party_on_application in application.third_parties.all():
        party = third_party_on_application.party
        documents_qs = PartyDocument.objects.filter(party=party).values_list("safe", flat=True)
        if documents_qs.exists():
            if None in documents_qs:
                return "We're still processing the third party document. Please submit again"
            elif False in documents_qs:
                return "To submit the application, attach a document that does not contain a virus to the end user"


def siel_ultimate_end_users_validator(application):
    """If ultimate end users are required and they added any documents check if they are all valid"""
    error = None

    ultimate_end_user_required = application.goods.filter(
        Q(is_good_incorporated=True) | Q(is_onward_incorporated=True)
    ).exists()

    if ultimate_end_user_required and application.ultimate_end_users.count() == 0:
        error = "To submit the application, add an ultimate end-user"
    else:
        end_user_id = application.end_user.party.id
        # We make sure that an ultimate end user is not also the end user
        if end_user_id in list(application.ultimate_end_users.values_list("id", flat=True)):
            error = "To submit the application, an ultimate end-user cannot be the same as the end user"

    return error


def siel_security_approvals_validator(application):
    error = "To submit the application, complete the 'Do you have a security approval?' section"

    return error if application.is_mod_security_approved is None else None


def siel_goods_validator(application):

    if application.goods.count() == 0:
        return "To submit the application, add a product"

    goods = application.goods.values_list("good", flat=True)
    document_statuses = GoodDocument.objects.filter(good__in=goods).values_list("safe", flat=True)

    # If safe field value is None, then the document hasn't been virus scanned yet
    if not all(item is not None for item in document_statuses):
        return "We're still processing a good document. Please submit again"

    # If safe is False, the file contains a virus
    if not all(document_statuses):
        return "To submit the application, attach a document that does not contain a virus to goods"


def siel_end_use_details_validator(application):
    if (
        application.is_military_end_use_controls is None
        or application.is_informed_wmd is None
        or application.is_suspected_wmd is None
        or application.is_eu_military is None
        or not application.intended_end_use
        or (application.is_eu_military and application.is_compliant_limitations_eu is None)
    ):
        return "To submit the application, complete the 'End use details' section"

    return None


def siel_route_of_goods_validator(application):
    if application.is_shipped_waybill_or_lading is None:
        return "To submit the application, complete the 'Route of products' section"

    return None


def siel_temporary_export_details_validator(application):
    if application.export_type == ApplicationExportType.PERMANENT:
        return None

    if (
        not application.temp_export_details
        or application.is_temp_direct_control is None
        or application.proposed_return_date is None
    ):
        return "To submit the application, add temporary export details"

    return None


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
        "consignee": siel_consignee_validator,
        "third_parties_documents": siel_third_parties_validator,
        "ultimate_end_user_documents": siel_ultimate_end_users_validator,
        "security_approvals": siel_security_approvals_validator,
        "goods": siel_goods_validator,
        "end_use_details": siel_end_use_details_validator,
        "route_of_goods": siel_route_of_goods_validator,
        "temporary_export_details": siel_temporary_export_details_validator,
    }
