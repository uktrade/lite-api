from django.db import transaction

from api.cases.enums import CaseTypeEnum
from api.staticdata.management.SeedCommand import SeedCommand

from api.staticdata.statuses.models import CaseStatus, CaseStatusCaseType

STATUSES_FILE = "lite_content/lite_api/case_statuses.csv"


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedcasestatuses
    """

    help = "Creates case statuses and case statuses on case types"
    info = "Seeding case statuses"
    seed_command = "seedcasestatuses"
    force_help_message = """Running this command will likely overwrite changes made to CaseStatus records.  ONLY DO THIS IF YOU REALLY MEAN TO.
    Use the --force flag to acknowledge the risks and run."""

    STATUSES_ON_CASE_TYPES = {
        "00000000-0000-0000-0000-000000000001": ["application", "hmrc", "goods", "eua"],
        "00000000-0000-0000-0000-000000000002": {"application"},
        "00000000-0000-0000-0000-000000000003": ["application", "hmrc", "goods", "eua"],
        "00000000-0000-0000-0000-000000000004": {"application"},
        "00000000-0000-0000-0000-000000000005": {"application"},
        "00000000-0000-0000-0000-000000000006": {"application"},
        "00000000-0000-0000-0000-000000000007": {"application"},
        "00000000-0000-0000-0000-000000000008": {"application"},
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help=self.force_help_message,
        )

    @transaction.atomic
    def operation(self, *args, **options):
        if not options["force"]:
            raise Exception(self.force_help_message)

        status_csv = self.read_csv(STATUSES_FILE)
        for row in status_csv:
            if row["workflow_sequence"] == "None":
                row["workflow_sequence"] = None

        self.update_or_create(CaseStatus, status_csv)

        case_type_list = CaseTypeEnum.CASE_TYPE_LIST

        # Use enum from populated case_types to assign new case_to_status
        for case_type in case_type_list:
            for key, value in self.STATUSES_ON_CASE_TYPES.items():
                # IF: sub-type is present in a STATUSES_ON_CASE_TYPE
                # OR IF: type is present but sub-type is not in a STATUSES_ON_CASE_TYPE (handles HMRC-applications)
                if case_type.sub_type in value or (case_type.type in value and case_type.sub_type not in value):
                    case_to_status_data = dict(case_type_id=str(case_type.id), status_id=key)
                    case_status_case_type = CaseStatusCaseType.objects.filter(**case_to_status_data)

                    if not case_status_case_type.exists():
                        CaseStatusCaseType.objects.create(**case_to_status_data)
                        self.print_created_or_updated(CaseStatusCaseType, case_to_status_data, is_created=True)
