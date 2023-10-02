import pytest
from parameterized import parameterized
from django.core.management import call_command, CommandError

from api.cases.models import Advice
from api.cases.tests.factories import FinalAdviceFactory, CaseFactory
from api.staticdata.denial_reasons.models import DenialReason
from api.staticdata.statuses.models import CaseStatus
from api.users.models import GovUser
from test_helpers.clients import DataTestClient


class TestCommand(DataTestClient):
    @parameterized.expand(
        [
            [
                [],
                {},
                "Error: the following arguments are required: advice_ids, --case_reference, --text, --denial_reasons",
            ],
            [
                ["some-advice-id"],
                {},
                "Error: the following arguments are required: --case_reference, --text, --denial_reasons",
            ],
            [
                ["some-advice-id"],
                {"case_reference": "some-ref"},
                "Error: the following arguments are required: --text, --denial_reasons",
            ],
            [
                ["some-advice-id"],
                {"case_reference": "some-ref", "text": "some text"},
                "Error: the following arguments are required: --denial_reasons",
            ],
            [
                ["some-advice-id"],
                {"case_reference": "some-ref", "denial_reasons": "12345"},
                "Error: the following arguments are required: --text",
            ],
        ]
    )
    def test_bad_arguments(self, args, kwargs, expected_error):
        with pytest.raises(CommandError) as exc_info:
            call_command("convert_nlr_advice_to_refuse", *args, **kwargs)
        assert exc_info.value.args[0] == expected_error

    @parameterized.expand(
        [
            [
                {"type": "refuse"},
                ["00000000-0000-0000-0000-000000000001"],
                {},
                "Expected to find 1 Advice records but found 0",
            ],
            [
                {"level": "user"},
                ["00000000-0000-0000-0000-000000000001"],
                {},
                "Expected to find 1 Advice records but found 0",
            ],
            [
                {},
                ["00000000-0000-0000-0000-000000000001"],
                {"case_reference": "some-bad-ref"},
                "Expected to find 1 Advice records but found 0",
            ],
            [{}, ["00000000-0000-0000-0000-000000000002"], {}, "Expected to find 1 Advice records but found 0"],
            [
                {},
                ["00000000-0000-0000-0000-000000000001"],
                {"denial_reasons": ["1", "bad-denial-id"]},
                "Expected to find 2 DenialReason records but found 1",
            ],
        ]
    )
    def test_no_matching_objects(self, advice_create_kwargs, command_args, command_kwargs, expected_error):
        case = CaseFactory(status=CaseStatus.objects.get(status="submitted"))
        base_advice_create_kwargs = {
            "id": "00000000-0000-0000-0000-000000000001",
            "case": case,
            "type": "no_licence_required",
            "user": GovUser.objects.first(),
        }
        advice_create_kwargs = {**base_advice_create_kwargs, **advice_create_kwargs}
        FinalAdviceFactory(
            **advice_create_kwargs,
        )
        denial_reason = DenialReason.objects.get(id="1")

        base_command_kwargs = {
            "case_reference": case.reference_code,
            "text": "some text",
            "denial_reasons": [denial_reason.id],
        }
        command_kwargs = {**base_command_kwargs, **command_kwargs}
        with pytest.raises(CommandError) as exc_info:
            call_command(
                "convert_nlr_advice_to_refuse",
                *command_args,
                **command_kwargs,
            )

        assert exc_info.value.args[0] == expected_error

    def test_successful_conversion(self):
        case = CaseFactory(status=CaseStatus.objects.get(status="submitted"))
        final_advice_1 = FinalAdviceFactory(
            id="00000000-0000-0000-0000-000000000001",
            case=case,
            type="no_licence_required",
            user=GovUser.objects.first(),
        )
        final_advice_2 = FinalAdviceFactory(
            id="00000000-0000-0000-0000-000000000002",
            case=case,
            type="no_licence_required",
            user=GovUser.objects.first(),
        )
        denial_reason_1 = DenialReason.objects.get(id="1")
        denial_reason_2 = DenialReason.objects.get(id="1a")

        call_command(
            "convert_nlr_advice_to_refuse",
            "00000000-0000-0000-0000-000000000001",
            "00000000-0000-0000-0000-000000000002",
            case_reference=case.reference_code,
            text="some text",
            denial_reasons=[denial_reason_1.id, denial_reason_2.id],
        )

        updated_advice = Advice.objects.filter(id__in=[final_advice_1.id, final_advice_2.id])
        for advice in updated_advice:
            assert advice.type == "refuse"
            assert advice.text == "some text"
            assert advice.is_refusal_note == True
            assert list(advice.denial_reasons.all().values_list("id", flat=True)) == ["1", "1a"]
