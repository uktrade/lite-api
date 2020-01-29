from django.http import Http404

from applications.enums import ApplicationType
from applications.models import GoodOnApplication, BaseApplication
from flags.enums import SystemFlags
from goods.enums import GoodStatus
from goodstype.models import GoodsType


def get_good_on_application(pk):
    try:
        return GoodOnApplication.objects.get(pk=pk)
    except GoodOnApplication.DoesNotExist:
        raise Http404


def update_submitted_application_good_statuses_and_flags(application: BaseApplication):
    """
    When an application is submitted;
    The 'not yet verified' system flag must be added to its Goods or GoodsTypes
    A Good's status must also be updated to 'SUBMITTED'
    """
    if application.application_type == ApplicationType.STANDARD_LICENCE:
        for good_on_application in GoodOnApplication.objects.filter(application=application):
            if good_on_application.good.status == GoodStatus.DRAFT:
                good_on_application.good.status = GoodStatus.SUBMITTED
                good_on_application.good.save()
            _add_good_not_yet_verified_system_flag_to_good(good_on_application.good)
    elif application.application_type == ApplicationType.OPEN_LICENCE:
        for goods_type_on_application in GoodsType.objects.filter(application=application):
            _add_good_not_yet_verified_system_flag_to_good(goods_type_on_application)


def _add_good_not_yet_verified_system_flag_to_good(good):
    if not good.flags.filter(id=SystemFlags.GOOD_NOT_YET_VERIFIED_ID).exists():
        good.flags.add(SystemFlags.GOOD_NOT_YET_VERIFIED_ID)
