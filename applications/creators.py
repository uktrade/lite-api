from applications.enums import ApplicationType
from applications.models import (
    CountryOnApplication,
    GoodOnApplication,
    SiteOnApplication,
    ExternalLocationOnApplication,
)
from content_strings.strings import get_string
from documents.models import Document
from goodstype.models import GoodsType
from parties.document.models import PartyDocument


def check_party_document(party, is_mandatory):
    """
    Checks for existence of and status of document (if it is mandatory) and return any errors
    """

    try:
        document = PartyDocument.objects.get(party=party)
    except Document.DoesNotExist:
        document = None
        if is_mandatory:
            return get_string(f"applications.standard.no_{party.type}_document_set")

    if document:
        if document.safe is None:
            return get_string(f"applications.standard.{party.type}_document_processing")
        elif not document.safe:
            return get_string(f"applications.standard.{party.type}_document_infected")
        else:
            return None


def check_parties_documents(parties, is_mandatory=True):
    for party in parties:
        error = check_party_document(party, is_mandatory)
        if error:
            return error
    return None


def check_party_error(party, object_not_found_error, is_document_mandatory=True):
    if not party:
        return object_not_found_error
    else:
        document_error = check_party_document(party, is_document_mandatory)
        if document_error:
            return document_error


def _validate_end_user(draft, errors):
    end_user_errors = check_party_error(
        draft.end_user,
        object_not_found_error=get_string("applications.standard.no_end_user_set"),
        is_document_mandatory=True,
    )
    if end_user_errors:
        errors["end_user"] = end_user_errors

    return errors


def _validate_consignee(draft, errors):
    consignee_errors = check_party_error(
        draft.consignee,
        object_not_found_error=get_string("applications.standard.no_consignee_set"),
        is_document_mandatory=True,
    )
    if consignee_errors:
        errors["consignee"] = consignee_errors

    return errors


def _validate_goods_types(draft, errors):
    results = GoodsType.objects.filter(application=draft)
    if not results:
        errors["goods"] = get_string("applications.open.no_goods_set")

    return errors


def _validate_standard_licence(draft, errors):
    errors = _validate_end_user(draft, errors)
    errors = _validate_consignee(draft, errors)

    ultimate_end_user_documents_error = check_parties_documents(draft.ultimate_end_users.all(), is_mandatory=True)
    if ultimate_end_user_documents_error:
        errors["ultimate_end_user_documents"] = ultimate_end_user_documents_error

    third_parties_documents_error = check_parties_documents(draft.third_parties.all(), is_mandatory=False)
    if third_parties_documents_error:
        errors["third_parties_documents"] = third_parties_documents_error

    if not GoodOnApplication.objects.filter(application=draft):
        errors["goods"] = get_string("applications.standard.no_goods_set")

    ultimate_end_user_required = False
    if next(
        filter(lambda x: x.good.is_good_end_product is False, GoodOnApplication.objects.filter(application=draft),),
        None,
    ):
        ultimate_end_user_required = True

    if ultimate_end_user_required:
        if len(draft.ultimate_end_users.values_list()) == 0:
            errors["ultimate_end_users"] = get_string("applications.standard.no_ultimate_end_users_set")
        else:
            # We make sure that an ultimate end user is not also the end user
            for ultimate_end_user in draft.ultimate_end_users.values_list("id", flat=True):
                if "end_user" not in errors and str(ultimate_end_user) == str(draft.end_user.id):
                    errors["ultimate_end_users"] = get_string(
                        "applications.standard.matching_end_user_and_ultimate_end_user"
                    )

    return errors


def _validate_open_licence(draft, errors):
    if len(CountryOnApplication.objects.filter(application=draft)) == 0:
        errors["countries"] = get_string("applications.open.no_countries_set")

    errors = _validate_goods_types(draft, errors)

    return errors


def _validate_hmrc_query(draft, errors):
    errors = _validate_goods_types(draft, errors)
    errors = _validate_end_user(draft, errors)

    return errors


def validate_application_ready_for_submission(application):
    errors = {}

    # Site & External location errors
    if (
        not SiteOnApplication.objects.filter(application=application).exists()
        and not ExternalLocationOnApplication.objects.filter(application=application).exists()
    ):
        errors["location"] = get_string("applications.generic.no_location_set")

    # Perform additional validation and append errors if found
    if application.application_type == ApplicationType.STANDARD_LICENCE:
        _validate_standard_licence(application, errors)
    elif application.application_type == ApplicationType.OPEN_LICENCE:
        _validate_open_licence(application, errors)
    elif application.application_type == ApplicationType.HMRC_QUERY:
        _validate_hmrc_query(application, errors)
    else:
        errors["unsupported_application"] = "You can only validate a supported application type"

    return errors
