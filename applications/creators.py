from django.http import JsonResponse
from rest_framework import status

from applications.models import CountryOnApplication, SiteOnApplication, ExternalLocationOnApplication, \
    GoodOnApplication
from content_strings.strings import get_string
from drafts.models import CountryOnDraft, SiteOnDraft, ExternalLocationOnDraft, GoodOnDraft
from parties.document.models import EndUserDocument
from goods.enums import GoodStatus
from goodstype.models import GoodsType
from parties.models import Party, EndUser, UltimateEndUser


def create_goods_for_applications(draft, application):
    for good_on_draft in GoodOnDraft.objects.filter(draft=draft):
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
    for site_on_draft in SiteOnDraft.objects.filter(draft=draft):
        site_on_application = SiteOnApplication(
            site=site_on_draft.site,
            application=application)
        site_on_application.save()


def create_external_location_for_application(draft, application):
    for external_location_on_draft in ExternalLocationOnDraft.objects.filter(draft=draft):
        external_location_on_application = ExternalLocationOnApplication(
            external_location=external_location_on_draft.external_location,
            application=application)
        external_location_on_application.save()


def check_party_document(end_user):
    try:
        end_user_document = EndUserDocument.objects.get(end_user=end_user)
        if end_user_document.safe is None:
            return get_string('applications.standard.end_user_document_processing')
        elif not end_user_document.safe:
            return get_string('applications.standard.end_user_document_infected')
    except EndUserDocument.DoesNotExist:
        return get_string('applications.standard.no_end_user_document_set')
    return None


def create_standard_licence(draft, application, errors):
    """
    Create a standard licence application
    """
    end_user = EndUser.objects.get(draft=draft)
    if not end_user:
        errors['end_user'] = get_string('applications.standard.no_end_user_set')

    end_user_documents_error = check_party_document(end_user)
    if end_user_documents_error:
        errors['end_user_document'] = end_user_documents_error

    if not GoodOnDraft.objects.filter(draft=draft):
        errors['goods'] = get_string('applications.standard.no_goods_set')

    ultimate_end_user_required = False
    if next(filter(lambda x: x.good.is_good_end_product is False, GoodOnDraft.objects.filter(draft=draft)), None):
        ultimate_end_user_required = True

    if ultimate_end_user_required:
        ultimate_end_users = UltimateEndUser.objects.filter(draft=draft)
        if len(ultimate_end_users.values_list()) == 0:
            errors['ultimate_end_users'] = get_string('applications.standard.no_ultimate_end_users_set')
        else:
            # We make sure that an ultimate end user is not also the end user
            for ultimate_end_user in ultimate_end_users.values_list('id', flat=True):
                if 'end_user' not in errors and str(ultimate_end_user) == str(end_user.id):
                    errors['ultimate_end_users'] = get_string('applications.standard.matching_end_user_and_ultimate_end_user')

    if len(errors):
        return JsonResponse(data={'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    application.save()
    
    # Save associated end users, goods and sites
    end_user.application = application
    end_user.save()
    if ultimate_end_user_required:
        for ultimate_end_user in ultimate_end_users:
            ultimate_end_user.application = application
            ultimate_end_user.save()

    create_goods_for_applications(draft, application)
    create_site_for_application(draft, application)
    create_external_location_for_application(draft, application)
    return application


def create_open_licence(draft, application, errors):
    """
    Create an open licence application
    """
    if len(CountryOnDraft.objects.filter(draft=draft)) == 0:
        errors['countries'] = get_string('applications.open.no_countries_set')

    results = GoodsType.objects.filter(object_id=draft.id)
    if not results:
        errors['goods'] = get_string('applications.open.no_goods_set')

    if len(errors):
        return JsonResponse(data={'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    application.save()

    for goods_types_on_draft in results:
        goods_types_on_draft.object_id = application.id

    for country_on_draft in CountryOnDraft.objects.filter(draft=draft):
        CountryOnApplication(
            country=country_on_draft.country,
            application=application).save()

    create_site_for_application(draft, application)
    create_external_location_for_application(draft, application)
    return application
