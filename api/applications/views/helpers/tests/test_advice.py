from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.applications.views.helpers.advice import get_countersign_process_flags, remove_countersign_process_flags
from api.applications.tests.factories import PartyOnApplicationFactory
from api.flags.models import Flag
from lite_routing.routing_rules_internal.enums import FlagsEnum

from test_helpers.clients import DataTestClient


class TestAdviceHelpers(DataTestClient):
    def test_get_countersign_process_flags(self):
        process_flags = get_countersign_process_flags()
        all_flag_ids = [str(flag.id) for flag in process_flags]
        assert set(all_flag_ids) == set(
            [
                FlagsEnum.LU_COUNTER_REQUIRED,
                FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED,
            ]
        )

    def test_remove_countersign_process_flags(self):
        countersign_process_flags = Flag.objects.filter(
            id__in=[
                FlagsEnum.LU_COUNTER_REQUIRED,
                FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED,
            ],
        )
        # Create some parties on a standard application; one with all countersign flags, another with a single countersign flag
        # and a third one with no countersign flags at all
        party_on_application_1 = PartyOnApplicationFactory()
        party_on_application_1.party.flags.add(*countersign_process_flags)
        application = party_on_application_1.application
        party_on_application_2 = PartyOnApplicationFactory(application=application)
        party_on_application_2.party.flags.add(countersign_process_flags[0])
        party_on_application_3 = PartyOnApplicationFactory(application=application)
        case = application.get_case()
        # Ensure the countersign flags are present in all the flags for the case
        for flag in countersign_process_flags:
            assert flag in case.parameter_set()

        # Remove the countersign flags with the helper function
        remove_countersign_process_flags(application, case)

        # Ensure the countersign flags are no longer present for the case
        for flag in countersign_process_flags:
            assert flag not in case.parameter_set()

        lu_flag_removal_audit = Audit.objects.filter(verb=AuditType.DESTINATION_REMOVE_FLAGS)
        assert lu_flag_removal_audit.exists()
        audit_obj = lu_flag_removal_audit.first()
        assert audit_obj.target == case
        assert audit_obj.payload == {
            "removed_flags": ["LU Countersign Required", "LU senior countersign required"],
            "is_lu_countersign_finalise_case": True,
        }

    def test_remove_countersign_process_flags_no_flags_to_remove(self):
        countersign_process_flags = Flag.objects.filter(
            id__in=[
                FlagsEnum.LU_COUNTER_REQUIRED,
                FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED,
            ],
        )
        # Create a party on a standard application; with no countersign flags
        party_on_application_1 = PartyOnApplicationFactory()
        application = party_on_application_1.application
        case = application.get_case()

        # Remove the countersign flags with the helper function
        remove_countersign_process_flags(application, case)

        lu_flag_removal_audit = Audit.objects.filter(verb=AuditType.DESTINATION_REMOVE_FLAGS)
        assert not lu_flag_removal_audit.exists()
