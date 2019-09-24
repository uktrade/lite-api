from django.http import JsonResponse
from rest_framework import status

from applications.models import CountryOnApplication, SiteOnApplication, ExternalLocationOnApplication, \
    GoodOnApplication
from content_strings.strings import get_string
from documents.models import Document
from parties.document.models import PartyDocument
from goods.enums import GoodStatus
from goodstype.models import GoodsType


def create_goods_for_applications(draft, application):
    for good_on_draft in GoodOnApplication.objects.filter(draft=draft):
        good_on_application = GoodOnApplication(
            good=good_on_draft.good,
            application=application,
            quantity=good_on_draft.quantity,
            unit=good_on_draft.unit,
            value=good_on_draft.value)
        good_on_application.save()
        good_on_application.good.status = GoodStatus.SUBMITTED
        good_on_application.good.save()


def create_site_for_application(draft, application):
    for site_on_draft in SiteOnApplication.objects.filter(draft=draft):
        site_on_application = SiteOnApplication(
            site=site_on_draft.site,
            application=application)
        site_on_application.save()


def create_external_location_for_application(draft, application):
    for external_location_on_draft in ExternalLocationOnApplication.objects.filter(draft=draft):
        external_location_on_application = ExternalLocationOnApplication(
            external_location=external_location_on_draft.external_location,
            application=application)
        external_location_on_application.save()


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


def create_standard_licence(draft, application, errors):
    """
    Create a standard licence application
    """
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

    if not GoodOnApplication.objects.filter(draft=draft):
        errors['goods'] = get_string('applications.standard.no_goods_set')

    ultimate_end_user_required = False
    if next(filter(lambda x: x.good.is_good_end_product is False, GoodOnApplication.objects.filter(draft=draft)), None):
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

    if len(errors):
        return JsonResponse(data={'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    # Save associated end users, goods and sites
    application.end_user = draft.end_user
    application.ultimate_end_users.set(draft.ultimate_end_users.values_list('id', flat=True))
    application.consignee = draft.consignee
    application.third_parties.set(draft.third_parties.values_list('id', flat=True))
    application.save()

    create_goods_for_applications(draft, application)
    create_site_for_application(draft, application)
    create_external_location_for_application(draft, application)
    return application


def create_open_licence(draft, application, errors):
    """
    Create an open licence application
    """
    if len(CountryOnApplication.objects.filter(draft=draft)) == 0:
        errors['countries'] = get_string('applications.open.no_countries_set')

    results = GoodsType.objects.filter(object_id=draft.id)
    if not results:
        errors['goods'] = get_string('applications.open.no_goods_set')

    if len(errors):
        return JsonResponse(data={'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    # Save associated end users, goods and sites
    application.end_user = draft.end_user
    application.save()

    for goods_types_on_draft in results:
        goods_types_on_draft.object_id = application.id

    for country_on_draft in CountryOnApplication.objects.filter(draft=draft):
        CountryOnApplication(
            country=country_on_draft.country,
            application=application).save()

    create_site_for_application(draft, application)
    create_external_location_for_application(draft, application)
    return application
