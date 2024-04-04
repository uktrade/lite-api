from api.applications.enums import ApplicationExportType, GoodsTypeCategory
from api.applications.models import (
    ApplicationDocument,
    GoodOnApplication,
    SiteOnApplication,
    ExternalLocationOnApplication,
    StandardApplication,
)
from api.cases.enums import CaseTypeSubTypeEnum
from api.core.helpers import str_to_bool
from api.goods.models import GoodDocument
from lite_content.lite_api import strings
from api.parties.models import PartyDocument
from api.parties.enums import PartyType


def _validate_siel_locations(application, errors):
    old_locations_invalid = (
        not SiteOnApplication.objects.filter(application=application).exists()
        and not ExternalLocationOnApplication.objects.filter(application=application).exists()
        and not getattr(application, "have_goods_departed", False)
        and not getattr(application, "goodstype_category", None) == GoodsTypeCategory.CRYPTOGRAPHIC
    )

    new_locations_invalid = (
        not getattr(application, "export_type", False)
        and not getattr(application, "goods_recipients", False)
        and not getattr(application, "goods_starting_point", False)
        and getattr(application, "is_shipped_waybill_or_lading") is None
    )

    if old_locations_invalid and new_locations_invalid:
        errors["location"] = [strings.Applications.Generic.NO_LOCATION_SET]

    return errors


def _get_document_errors(documents, processing_error, virus_error):
    document_statuses = documents.values_list("safe", flat=True)

    # If safe is None, then the document hasn't been virus scanned yet
    if not all([safe is not None for safe in document_statuses]):
        return processing_error

    # If safe is False, the file contains a virus
    if not all(document_statuses):
        return virus_error


def check_party_document(party, is_mandatory):
    """
    Checks for existence of and status of document (if it is mandatory) and return any errors
    """
    documents_qs = PartyDocument.objects.filter(party=party).values_list("safe", flat=True)
    if not documents_qs.exists():
        # End-user document is mandatory but we are providing an option to not upload
        # if there is a valid reason
        if party.type == PartyType.END_USER and party.end_user_document_available is False:
            return None

        if is_mandatory:
            return getattr(strings.Applications.Standard, f"NO_{party.type.upper()}_DOCUMENT_SET")
        else:
            return None

    if None in documents_qs:
        return getattr(strings.Applications.Standard, f"{party.type.upper()}_DOCUMENT_PROCESSING")
    elif False in documents_qs:
        return getattr(strings.Applications.Standard, f"{party.type.upper()}_DOCUMENT_INFECTED")

    return None


def check_parties_documents(parties, is_mandatory=True):
    """Check a given list of parties all have documents if is_mandatory. Also checks all documents are safe"""

    for poa in parties:
        error = check_party_document(poa.party, is_mandatory)
        if error:
            return error
    return None


def check_party_error(party, object_not_found_error, is_mandatory, is_document_mandatory=True):
    """Check a given party exists and has a document if is_document_mandatory"""

    if is_mandatory and not party:
        return object_not_found_error
    elif party:
        document_error = check_party_document(party, is_document_mandatory)
        if document_error:
            return document_error


def _validate_end_user(draft, errors, is_mandatory, open_application=False):
    """Validates end user. If a document is mandatory, this is also validated."""

    # Document is only mandatory if application is standard permanent or HMRC query
    is_document_mandatory = (
        draft.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD
        and draft.export_type == ApplicationExportType.PERMANENT
    ) or draft.case_type.sub_type == CaseTypeSubTypeEnum.HMRC

    end_user_errors = check_party_error(
        draft.end_user.party if draft.end_user else None,
        object_not_found_error=strings.Applications.Standard.NO_END_USER_SET,
        is_mandatory=is_mandatory,
        is_document_mandatory=is_document_mandatory,
    )
    if end_user_errors:
        errors["end_user"] = [end_user_errors]

    return errors


def _validate_consignee(draft, errors, is_mandatory):
    """
    Checks there is an consignee if goods_recipients is set to VIA_CONSIGNEE or VIA_CONSIGNEE_AND_THIRD_PARTIES
    (with a document if is_document_mandatory)
    """
    # This logic includes old style applications where the goods_recipients field will be ""
    if draft.goods_recipients != StandardApplication.DIRECT_TO_END_USER:
        consignee_errors = check_party_error(
            draft.consignee.party if draft.consignee else None,
            object_not_found_error=strings.Applications.Standard.NO_CONSIGNEE_SET,
            is_mandatory=is_mandatory,
            is_document_mandatory=False,
        )
        if consignee_errors:
            errors["consignee"] = [consignee_errors]
    return errors


def _validate_security_approvals(draft, errors, is_mandatory):
    """Checks there are security approvals for the draft"""
    if is_mandatory:
        if draft.is_mod_security_approved is None:
            errors["security_approvals"] = [
                "To submit the application, complete the 'Do you have a security approval?' section"
            ]
    return errors


def _validate_ultimate_end_users(draft, errors, is_mandatory, open_application=False):
    """
    Checks all ultimate end users have documents if is_mandatory is True.
    Also checks that at least one ultimate_end_user is present if there is an incorporated good
    """
    # Document is always optional even if there are incorporated goods
    ultimate_end_user_documents_error = check_parties_documents(draft.ultimate_end_users.all(), is_mandatory=False)
    if ultimate_end_user_documents_error:
        errors["ultimate_end_user_documents"] = [ultimate_end_user_documents_error]

    if is_mandatory:
        if open_application:
            ultimate_end_user_required = True in [
                goodstype.is_good_incorporated for goodstype in list(draft.goods_type.all())
            ]
        else:
            ultimate_end_user_required = GoodOnApplication.objects.filter(
                application=draft, is_good_incorporated=True
            ).exists()

        if ultimate_end_user_required:
            if len(draft.ultimate_end_users.values_list()) == 0:
                errors["ultimate_end_users"] = ["To submit the application, add an ultimate end-user"]
            # goods_types are used in open applications and we don't have end_users in them currently.
            elif not open_application:
                # We make sure that an ultimate end user is not also the end user
                for ultimate_end_user in draft.ultimate_end_users.values_list("id", flat=True):
                    if "end_user" not in errors and str(ultimate_end_user) == str(draft.end_user.party.id):
                        errors["ultimate_end_users"] = [
                            "To submit the application, an ultimate end-user cannot be the same as the end user"
                        ]

    return errors


def _validate_end_use_details(draft, errors, application_type):
    if application_type in [CaseTypeSubTypeEnum.STANDARD, CaseTypeSubTypeEnum.OPEN]:
        if (
            draft.is_military_end_use_controls is None
            or draft.is_informed_wmd is None
            or draft.is_suspected_wmd is None
            or not draft.intended_end_use
        ) and not getattr(draft, "goodstype_category", None) == GoodsTypeCategory.CRYPTOGRAPHIC:
            errors["end_use_details"] = [strings.Applications.Generic.NO_END_USE_DETAILS]

        if application_type == CaseTypeSubTypeEnum.STANDARD:
            if draft.is_eu_military is None:
                errors["end_use_details"] = [strings.Applications.Generic.NO_END_USE_DETAILS]
            elif draft.is_eu_military and draft.is_compliant_limitations_eu is None:
                errors["end_use_details"] = [strings.Applications.Generic.NO_END_USE_DETAILS]

    elif application_type == CaseTypeSubTypeEnum.F680:
        if not draft.intended_end_use:
            errors["end_use_details"] = [strings.Applications.Generic.NO_END_USE_DETAILS]

    return errors


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


def _validate_temporary_export_details(draft, errors):
    if (
        draft.case_type.sub_type in [CaseTypeSubTypeEnum.STANDARD, CaseTypeSubTypeEnum.OPEN]
        and draft.export_type == ApplicationExportType.TEMPORARY
    ):
        if not draft.temp_export_details or draft.is_temp_direct_control is None or draft.proposed_return_date is None:
            errors["temporary_export_details"] = [strings.Applications.Generic.NO_TEMPORARY_EXPORT_DETAILS]

    return errors


def _validate_third_parties(draft, errors, is_mandatory):
    """Checks all third parties have documents if is_mandatory is True"""

    third_parties_documents_error = check_parties_documents(draft.third_parties.all(), is_mandatory)
    if third_parties_documents_error:
        errors["third_parties_documents"] = [third_parties_documents_error]

    return errors


def _validate_goods(draft, errors, is_mandatory):
    """Checks Goods"""

    goods_on_application = GoodOnApplication.objects.filter(application=draft)

    if is_mandatory:
        if not goods_on_application:
            errors["goods"] = [strings.Applications.Standard.NO_GOODS_SET]

    # Check goods documents
    if goods_on_application.exists():
        goods = goods_on_application.values_list("good", flat=True)
        document_errors = _get_document_errors(
            GoodDocument.objects.filter(good__in=goods),
            processing_error=strings.Applications.Standard.GOODS_DOCUMENT_PROCESSING,
            virus_error=strings.Applications.Standard.GOODS_DOCUMENT_INFECTED,
        )
        if document_errors:
            errors["goods"] = [document_errors]

    return errors


def _validate_standard_licence(draft, errors):
    """Checks that a standard licence has all party types & goods"""

    errors = _validate_siel_locations(draft, errors)
    errors = _validate_end_user(draft, errors, is_mandatory=True)
    errors = _validate_security_approvals(draft, errors, is_mandatory=True)
    errors = _validate_consignee(draft, errors, is_mandatory=True)
    errors = _validate_third_parties(draft, errors, is_mandatory=False)
    errors = _validate_goods(draft, errors, is_mandatory=True)
    errors = _validate_ultimate_end_users(draft, errors, is_mandatory=True)
    errors = _validate_end_use_details(draft, errors, draft.case_type.sub_type)
    errors = _validate_route_of_goods(draft, errors)
    errors = _validate_temporary_export_details(draft, errors)

    return errors


def _validate_f680(draft, errors):
    # placeholder as we don't want anything required in the tasklist currently
    return errors


def _validate_route_of_goods(draft, errors):
    if (
        draft.is_shipped_waybill_or_lading is None
        and not getattr(draft, "goodstype_category", None) == GoodsTypeCategory.CRYPTOGRAPHIC
    ):
        errors["route_of_goods"] = [strings.Applications.Generic.NO_ROUTE_OF_GOODS]
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

    # Perform additional validation and append errors if found
    enabled_casetypes = [CaseTypeSubTypeEnum.STANDARD, CaseTypeSubTypeEnum.F680]

    if application.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD:
        _validate_standard_licence(application, errors)
    if application.case_type.sub_type == CaseTypeSubTypeEnum.F680:
        _validate_f680(application, errors)
    else:
        errors["unsupported_application"] = ["You can only validate a supported application type"]

    errors = _validate_additional_documents(application, errors)

    return errors
