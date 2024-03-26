from api.applications.enums import ApplicationExportType
from api.cases.enums import CaseTypeSubTypeEnum
from api.parties.models import PartyDocument
from api.parties.enums import PartyType

from lite_content.lite_api import strings


def siel_end_user_validator(application):
    errors = {"end_user": []}

    # perform validation checks

    return errors


class BaseApplicationValidator:
    config = {}

    def __init__(self, application):
        self.application = application

    def validate(self):
        all_errors = {}
        for _, func in self.config.items():
            errors = func(self.application)
            all_errors = {**errors, **all_errors}

        return all_errors


class StandardApplicationValidator(BaseApplicationValidator):
    config = {
        "end_user": siel_end_user_validator,
        # more to follow
    }


class ApplicationValidator:
    def __init__(self, application):
        self.application = application

    def validate(self):
        errors = {}
        if not self.application:
            raise ValueError("Invalid application")

        if self.application.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD:
            errors = StandardApplicationValidator(self.application).validate()
        else:
            raise NotImplementedError("Only SIEL applications are supported")

        return errors
