from django.http import JsonResponse
from rest_framework import status

from applications.models import CountryOnApplication, SiteOnApplication, ExternalLocationOnApplication, \
    GoodOnApplication
from content_strings.strings import get_string
from documents.models import Document
from parties.document.models import PartyDocument
from goodstype.models import GoodsType


def check_party_document(party):
    try:
        document = PartyDocument.objects.get(party=party)
    except Document.DoesNotExist:
        return get_string('applications.standard.no_{}_document_set'.format(party.type))

    if not document:
        return get_string('applications.standard.no_{}_document_set'.format(party.type))
    elif document.safe is None:
        return get_string('applications.standard.{}_document_processing'.format(party.type))
    elif not document.safe:
        return get_string('applications.standard.{}_document_infected'.format(party.type))
    else:
        return None


def check_ultimate_end_user_documents_for_draft(draft):
    ultimate_end_users = draft.ultimate_end_users.all()
    for ultimate_end_user in ultimate_end_users:
        error = check_party_document(ultimate_end_user)
        if error:
            return error
    return None


def validate_standard_licence(draft, errors):
    if not draft.end_user:
        errors['end_user'] = get_string('applications.standard.no_end_user_set')
    else:
        end_user_document_error = check_party_document(draft.end_user)
        if end_user_document_error:
            errors['end_user_document'] = end_user_document_error

    if not draft.consignee:
        errors['consignee'] = get_string('applications.standard.no_consignee_set')
    else:
        consignee_document_error = check_party_document(draft.consignee)
        if consignee_document_error:
            errors['consignee_document'] = consignee_document_error

    ultimate_end_user_documents_error = check_ultimate_end_user_documents_for_draft(draft)
    if ultimate_end_user_documents_error:
        errors['ultimate_end_user_documents'] = ultimate_end_user_documents_error

    if not GoodOnApplication.objects.filter(application=draft):
        errors['goods'] = get_string('applications.standard.no_goods_set')

    ultimate_end_user_required = False
    if next(filter(
            lambda x: x.good.is_good_end_product is False, GoodOnApplication.objects.filter(application=draft)), None):
        ultimate_end_user_required = True

    if ultimate_end_user_required:
        if len(draft.ultimate_end_users.values_list()) == 0:
            errors['ultimate_end_users'] = get_string('applications.standard.no_ultimate_end_users_set')
        else:
            # We make sure that an ultimate end user is not also the end user
            for ultimate_end_user in draft.ultimate_end_users.values_list('id', flat=True):
                if 'end_user' not in errors and str(ultimate_end_user) == str(draft.end_user.id):
                    errors['ultimate_end_users'] = get_string(
                        'applications.standard.matching_end_user_and_ultimate_end_user')

    return errors


def validate_open_licence(draft, errors):
    if len(CountryOnApplication.objects.filter(application=draft)) == 0:
        errors['countries'] = get_string('applications.open.no_countries_set')

    results = GoodsType.objects.filter(application=draft)
    if not results:
        errors['goods'] = get_string('applications.open.no_goods_set')

    return errors
