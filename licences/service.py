from licences.enums import LicenceStatus
from licences.models import Licence
from static.control_list_entries.serializers import ControlListEntrySerializer


def get_case_licences(case):
    licences = (
        Licence.objects.prefetch_related(
            "goods", "goods__good", "goods__good__good", "goods__good__good__control_list_entries"
        )
        .filter(application=case)
        .order_by("created_at")
    )
    return [
        {
            "id": str(licence.id),
            "reference_code": licence.reference_code,
            "status": LicenceStatus.to_str(licence.status),
            "goods": [
                {
                    "description": licence_good.good.good.description,
                    "control_list_entries": ControlListEntrySerializer(
                        licence_good.good.good.control_list_entries.all(), many=True
                    ).data,
                    "quantity": licence_good.quantity,
                    "usage": licence_good.usage,
                }
                for licence_good in licence.goods.all()
            ],
        }
        for licence in licences
    ]
