from django.http import Http404

from api.applications.models import GoodOnApplication, BaseApplication
from api.cases.enums import CaseTypeSubTypeEnum
from api.flags.enums import SystemFlags
from api.goods.enums import GoodStatus
from api.goodstype.models import GoodsType


def add_goods_flags_to_submitted_application(application: BaseApplication):
    """
    When an application is submitted;
    The 'not yet verified' system flag must be added to its Goods or GoodsTypes
    A Good's status must also be updated to 'SUBMITTED'
    """
    if application.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD:
        for good_on_application in GoodOnApplication.objects.filter(application=application):
            if good_on_application.good.status == GoodStatus.DRAFT:
                good_on_application.good.status = GoodStatus.SUBMITTED
                good_on_application.good.save()
                _add_good_not_yet_verified_system_flag_to_good(good_on_application.good)
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.OPEN:
        for goods_type_on_application in GoodsType.objects.filter(application=application):
            _add_good_not_yet_verified_system_flag_to_good(goods_type_on_application)


def _add_good_not_yet_verified_system_flag_to_good(good):
    if not good.flags.filter(id=SystemFlags.GOOD_NOT_YET_VERIFIED_ID).exists():
        good.flags.add(SystemFlags.GOOD_NOT_YET_VERIFIED_ID)
