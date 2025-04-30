from api.organisations.libraries.get_organisation import get_request_user_organisation
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


def organisation_serializer_context_processor(request):
    return {
        "organisation": get_request_user_organisation(request),
    }


def draft_status_serializer_context_processor(request):
    return {
        "default_status": get_case_status_by_status(CaseStatusEnum.DRAFT),
    }


class CaseTypeSerializerContextProcessor:
    def __init__(self, case_type_id):
        self.case_type_id = case_type_id

    def __call__(self, request):
        return {
            "case_type_id": self.case_type_id,
        }
