from compat import JsonResponse
from rest_framework import status
from django.utils import timezone


from drafts.models import GoodOnDraft
from goods.enums import GoodStatus
from organisations.libraries.get_organisation import get_organisation_by_user
from queries.control_list_classifications.models import ControlListClassificationQuery


def bad_request_if_submitted(_, __, good):
    if good.status == GoodStatus.SUBMITTED:
        return JsonResponse(data={'errors': 'This good is already on a submitted application'},
                            status=status.HTTP_400_BAD_REQUEST)


def if_status_unsure_remove_from_draft(_, data, good):
    if data.get('is_good_controlled') == 'unsure':
        for good_on_draft in GoodOnDraft.objects.filter(good=good):
            good_on_draft.delete()


def add_organisation_to_data(request, data, __):
    data['organisation'] = get_organisation_by_user(request.user).id


def update_notifications(request, _, good):
    try:
        query = ControlListClassificationQuery.objects.get(good=good)
        request.user.notification_set.filter(case_note__case__query=query).update(
            viewed_at=timezone.now()
        )
        request.user.notification_set.filter(query=query.id).update(
            viewed_at=timezone.now()
        )
    except ControlListClassificationQuery.DoesNotExist:
        pass
