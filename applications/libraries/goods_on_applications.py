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


def update_good_statuses_and_flags_on_application(application: BaseApplication):
    if application.application_type == ApplicationType.STANDARD_LICENCE:
        for good_on_application in GoodOnApplication.objects.filter(application=application):
            if good_on_application.good.status == GoodStatus.DRAFT:
                good_on_application.good.status = GoodStatus.SUBMITTED
                if not good_on_application.good.flags.filter(id=SystemFlags.GOOD_NOT_YET_VERIFIED_ID).exists():
                    good_on_application.good.flags.add(SystemFlags.GOOD_NOT_YET_VERIFIED_ID)
                good_on_application.good.save()
    elif application.application_type == ApplicationType.OPEN_LICENCE:
        for goods_type_on_application in GoodsType.objects.filter(application=application):
            if not goods_type_on_application.flags.filter(id=SystemFlags.GOOD_NOT_YET_VERIFIED_ID).exists():
                goods_type_on_application.flags.add(SystemFlags.GOOD_NOT_YET_VERIFIED_ID)
            goods_type_on_application.save()
