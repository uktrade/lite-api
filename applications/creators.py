from django.utils import timezone

from applications.models import (
    CountryOnApplication,
    GoodOnApplication,
    SiteOnApplication,
    ExternalLocationOnApplication,
)
from cases.enums import CaseTypeSubTypeEnum
from documents.models import Document
from goodstype.models import GoodsType
from lite_content.lite_api import strings
from parties.models import PartyDocument


def _validate_locations(application, errors):
    """ Site & External location errors """
    if (
        not SiteOnApplication.objects.filter(application=application).exists()
        and not ExternalLocationOnApplication.objects.filter(application=application).exists()
        and not getattr(application, "have_goods_departed", False)
    ):
        errors["location"] = strings.Applications.Generic.NO_LOCATION_SET

    return errors


def check_party_document(party, is_mandatory):
    """
    Checks for existence of and status of document (if it is mandatory) and return any errors
    """

    try:
        document = PartyDocument.objects.get(party=party)
    except Document.DoesNotExist:
        document = None
        if is_mandatory:
            return getattr(strings.Applications.Standard, f"NO_{party.type.upper()}_DOCUMENT_SET")

    if document:
        if document.safe is None:
            return getattr(strings.Applications.Standard, f"{party.type.upper()}_DOCUMENT_PROCESSING")
        elif not document.safe:
            return getattr(strings.Applications.Standard, f"{party.type.upper()}_DOCUMENT_INFECTED")
        else:
            return None


def check_parties_documents(parties, is_mandatory=True):
    """ Check a given list of parties all have documents if is_mandatory. Also checks all documents are safe """

    for poa in parties:
        error = check_party_document(poa.party, is_mandatory)
        if error:
            return error
    return None


def check_party_error(party, object_not_found_error, is_mandatory, is_document_mandatory=True):
    """ Check a given party exists and has a document if is_document_mandatory """

    if is_mandatory and not party:
        return object_not_found_error
    elif party:
        document_error = check_party_document(party, is_document_mandatory)
        if document_error:
            return document_error


def _validate_end_user(draft, errors, is_mandatory):
    """ Checks there is an end user (with a document if is_document_mandatory) """

    end_user_errors = check_party_error(
        draft.end_user.party if draft.end_user else None,
        object_not_found_error=strings.Applications.Standard.NO_END_USER_SET,
        is_mandatory=is_mandatory,
        is_document_mandatory=True,
    )
    if end_user_errors:
        errors["end_user"] = end_user_errors

    return errors


def _validate_consignee(draft, errors, is_mandatory):
    """ Checks there is an consignee (with a document if is_document_mandatory) """

    consignee_errors = check_party_error(
        draft.consignee.party if draft.consignee else None,
        object_not_found_error=strings.Applications.Standard.NO_CONSIGNEE_SET,
        is_mandatory=is_mandatory,
        is_document_mandatory=True,
    )
    if consignee_errors:
        errors["consignee"] = consignee_errors

    return errors


def _validate_countries(draft, errors, is_mandatory):
    """ Checks there are countries for the draft """

    if is_mandatory:
        if len(CountryOnApplication.objects.filter(application=draft)) == 0:
            errors["countries"] = strings.Applications.Open.NO_COUNTRIES_SET

    return errors


def _validate_goods_types(draft, errors, is_mandatory):
    """ Checks there are GoodsTypes for the draft """

    if is_mandatory:
        results = GoodsType.objects.filter(application=draft)
        if not results:
            errors["goods"] = strings.Applications.Open.NO_GOODS_SET

    return errors


def _validate_ultimate_end_users(draft, errors, is_mandatory):
    """
    Checks all ultimate end users have documents if is_mandatory is True.
    Also checks that at least one ultimate_end_user is present if there is an incorporated good
    """

    ultimate_end_user_documents_error = check_parties_documents(draft.ultimate_end_users.all(), is_mandatory)
    if ultimate_end_user_documents_error:
        errors["ultimate_end_user_documents"] = ultimate_end_user_documents_error

    if is_mandatory:
        ultimate_end_user_required = GoodOnApplication.objects.filter(
            application=draft, is_good_incorporated=True
        ).exists()

        if ultimate_end_user_required:
            if len(draft.ultimate_end_users.values_list()) == 0:
                errors["ultimate_end_users"] = strings.Applications.Standard.NO_ULTIMATE_END_USERS_SET
            else:
                # We make sure that an ultimate end user is not also the end user
                for ultimate_end_user in draft.ultimate_end_users.values_list("id", flat=True):
                    if "end_user" not in errors and str(ultimate_end_user) == str(draft.end_user.party.id):
                        errors[
                            "ultimate_end_users"
                        ] = strings.Applications.Standard.MATCHING_END_USER_AND_ULTIMATE_END_USER

    return errors


def _validate_end_use_details(draft, errors, application_type):
    if application_type in [CaseTypeSubTypeEnum.STANDARD, CaseTypeSubTypeEnum.OPEN]:
        if (
            draft.is_military_end_use_controls is None
            or draft.is_informed_wmd is None
            or draft.is_suspected_wmd is None
            or not draft.intended_end_use
        ):
            errors["end_use_details"] = strings.Applications.Generic.NO_END_USE_DETAILS

        if application_type == CaseTypeSubTypeEnum.STANDARD:
            if draft.is_eu_military is None:
                errors["end_use_details"] = strings.Applications.Generic.NO_END_USE_DETAILS
            elif draft.is_eu_military and draft.is_compliant_limitations_eu is None:
                errors["end_use_details"] = strings.Applications.Generic.NO_END_USE_DETAILS

    elif application_type == CaseTypeSubTypeEnum.F680:
        if not draft.intended_end_use:
            errors["end_use_details"] = strings.Applications.Generic.NO_END_USE_DETAILS

    return errors


def _validate_additional_information(draft, errors):
    required_fields = [
        "expedited",
        "foreign_technology",
        "locally_manufactured",
        "mtcr_type",
        "electronic_warfare_requirement",
        "uk_service_equipment",
        "prospect_value",
    ]
    required_secondary_fields = {
        "foreign_technology": "foreign_technology_description",
        "expedited": "expedited_date",
        "locally_manufactured": "locally_manufactured_description",
    }

    for field in required_fields:
        if getattr(draft, field) is None or getattr(draft, field) == "":
            errors["additional_information"] = strings.Applications.F680.AdditionalInformation.Errors.MUST_BE_COMPLETED
        if getattr(draft, field) is True:
            secondary_field = required_secondary_fields.get(field, False)
            if secondary_field and not getattr(draft, secondary_field):
                errors[
                    "additional_information"
                ] = strings.Applications.F680.AdditionalInformation.Errors.MUST_BE_COMPLETED

    today = timezone.now().date()

    if getattr(draft, "expedited_date") and getattr(draft, "expedited_date") < today:
        errors["questions"] = strings.Applications.F680.AdditionalInformation.Errors.PAST_DATE

    return errors


def _validate_third_parties(draft, errors, is_mandatory):
    """ Checks all third parties have documents if is_mandatory is True """

    third_parties_documents_error = check_parties_documents(draft.third_parties.all(), is_mandatory)
    if third_parties_documents_error:
        errors["third_parties_documents"] = third_parties_documents_error

    return errors


def _validate_has_goods(draft, errors, is_mandatory):
    """ Checks draft has Goods """

    if is_mandatory:
        if not GoodOnApplication.objects.filter(application=draft):
            errors["goods"] = strings.Applications.Standard.NO_GOODS_SET

    return errors


def _validate_has_clearance_level(draft, errors, is_mandatory):
    """ Checks draft has clearance level """

    if is_mandatory:
        if not draft.clearance_level:
            errors["clearance_level"] = strings.Applications.Standard.NO_CLEARANCE_LEVEL

    return errors


def _validate_exhibition_details(draft, errors):
    """ Checks that an exhibition clearance has details """

    if not all(getattr(draft, attribute) for attribute in ["title", "first_exhibition_date", "required_by_date"]):
        errors["details"] = strings.Applications.Exhibition.Error.NO_DETAILS

    return errors


def _validate_standard_licence(draft, errors):
    """ Checks that a standard licence has all party types & goods """

    errors = _validate_locations(draft, errors)
    errors = _validate_end_user(draft, errors, is_mandatory=True)
    errors = _validate_consignee(draft, errors, is_mandatory=True)
    errors = _validate_third_parties(draft, errors, is_mandatory=False)
    errors = _validate_has_goods(draft, errors, is_mandatory=True)
    errors = _validate_ultimate_end_users(draft, errors, is_mandatory=True)
    errors = _validate_end_use_details(draft, errors, draft.case_type.sub_type)

    return errors


def _validate_exhibition_clearance(draft, errors):
    """ Checks that an exhibition clearance has goods, locations and details """

    errors = _validate_exhibition_details(draft, errors)
    errors = _validate_has_goods(draft, errors, is_mandatory=True)
    errors = _validate_locations(draft, errors)

    return errors


def _validate_gifting_clearance(draft, errors):
    """ Checks that a gifting clearance has an end_user and goods """

    errors = _validate_end_user(draft, errors, is_mandatory=True)
    errors = _validate_third_parties(draft, errors, is_mandatory=False)
    errors = _validate_has_goods(draft, errors, is_mandatory=True)

    if draft.consignee:
        errors["consignee"] = strings.Applications.Gifting.CONSIGNEE

    if draft.ultimate_end_users:
        errors["ultimate_end_users"] = strings.Applications.Gifting.ULTIMATE_END_USERS

    if SiteOnApplication.objects.filter(application=draft).exists():
        errors["location"] = strings.Applications.Gifting.LOCATIONS

    return errors


def _validate_f680_clearance(draft, errors):
    """ F680 require goods and at least 1 end user or third party """

    errors = _validate_has_clearance_level(draft, errors, is_mandatory=True)
    errors = _validate_has_goods(draft, errors, is_mandatory=True)
    errors = _validate_end_user(draft, errors, is_mandatory=False)
    errors = _validate_third_parties(draft, errors, is_mandatory=False)
    errors = _validate_additional_information(draft, errors)
    errors = _validate_end_use_details(draft, errors, draft.case_type.sub_type)

    if not draft.end_user and not draft.third_parties.exists():
        errors["party"] = strings.Applications.F680.NO_END_USER_OR_THIRD_PARTY

    if draft.consignee:
        errors["consignee"] = strings.Applications.F680.CONSIGNEE

    if draft.ultimate_end_users:
        errors["ultimate_end_users"] = strings.Applications.F680.ULTIMATE_END_USERS

    if SiteOnApplication.objects.filter(application=draft).exists():
        errors["location"] = strings.Applications.F680.LOCATIONS

    if not draft.types.exists():
        errors["types"] = strings.Applications.F680.NO_CLEARANCE_TYPE

    return errors


def _validate_open_licence(draft, errors):
    """ Open licences require countries & goods types """

    errors = _validate_locations(draft, errors)
    errors = _validate_countries(draft, errors, is_mandatory=True)
    errors = _validate_goods_types(draft, errors, is_mandatory=True)
    errors = _validate_end_use_details(draft, errors, draft.case_type.sub_type)

    return errors


def _validate_hmrc_query(draft, errors):
    """ HMRC queries require goods types & an end user """

    errors = _validate_locations(draft, errors)
    errors = _validate_goods_types(draft, errors, is_mandatory=True)
    errors = _validate_end_user(draft, errors, is_mandatory=True)

    return errors


def validate_application_ready_for_submission(application):
    errors = {}

    # Perform additional validation and append errors if found
    if application.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD:
        _validate_standard_licence(application, errors)
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.OPEN:
        _validate_open_licence(application, errors)
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.HMRC:
        _validate_hmrc_query(application, errors)
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.EXHIBITION:
        _validate_exhibition_clearance(application, errors)
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.GIFTING:
        _validate_gifting_clearance(application, errors)
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.F680:
        _validate_f680_clearance(application, errors)
    else:
        errors["unsupported_application"] = "You can only validate a supported application type"

    return errors
