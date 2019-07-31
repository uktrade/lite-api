from django.http import JsonResponse
from rest_framework import status

from applications.models import CountryOnApplication, SiteOnApplication, ExternalLocationOnApplication, \
    GoodOnApplication
from content_strings.strings import get_string
from drafts.models import CountryOnDraft, SiteOnDraft, ExternalLocationOnDraft, GoodOnDraft
from goods.enums import GoodStatus
from goodstype.models import GoodsType


def create_standard_licence(draft, application, errors):
    """
    Create a standard licence application
    """
    if not draft.end_user:
        errors['end_user'] = get_string('applications.standard.no_end_user_set')

    if not GoodOnDraft.objects.filter(draft=draft):
        errors['goods'] = get_string('applications.standard.no_goods_set')

    ultimate_end_user_required = False
    if next(filter(lambda x: x.good.is_good_end_product is False, GoodOnDraft.objects.filter(draft=draft)), None):
        ultimate_end_user_required = True

    if ultimate_end_user_required:
        if len(draft.ultimate_end_users.values_list()) == 0:
            errors['ultimate_end_users'] = get_string('applications.standard.no_ultimate_end_users_set')
        else:
            # We make sure that an ultimate end user is not also the end user
            for ultimate_end_user in draft.ultimate_end_users.values_list('id', flat=True):
                if 'end_user' not in errors and str(ultimate_end_user) == str(draft.end_user.id):
                    errors['ultimate_end_users'] = get_string('applications.standard.matching_end_user_and_ultimate_end_user')

    if len(errors):
        return JsonResponse(data={'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    # Save associated end users, goods and sites
    application.end_user = draft.end_user
    application.ultimate_end_users.set(draft.ultimate_end_users.values_list('id', flat=True))
    application.save()

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

    for site_on_draft in SiteOnDraft.objects.filter(draft=draft):
        site_on_application = SiteOnApplication(
            site=site_on_draft.site,
            application=application)
        site_on_application.save()

    for external_location_on_draft in ExternalLocationOnDraft.objects.filter(draft=draft):
        external_location_on_application = ExternalLocationOnApplication(
            external_location=external_location_on_draft.external_location,
            application=application)
        external_location_on_application.save()

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

    # Save associated end users, goods and sites
    application.end_user = draft.end_user
    application.save()

    for goods_types_on_draft in results:
        goods_types_on_draft.object_id = application.id

    for country_on_draft in CountryOnDraft.objects.filter(draft=draft):
        CountryOnApplication(
            country=country_on_draft.country,
            application=application).save()

    for site_on_draft in SiteOnDraft.objects.filter(draft=draft):
        site_on_application = SiteOnApplication(
            site=site_on_draft.site,
            application=application)
        site_on_application.save()

    for external_location_on_draft in ExternalLocationOnDraft.objects.filter(draft=draft):
        external_location_on_application = ExternalLocationOnApplication(
            external_location=external_location_on_draft.external_location,
            application=application)
        external_location_on_application.save()

    return application
