from django.db import migrations


def create_case_sub_status_records(apps, schema_editor):
    CaseStatus = apps.get_model("statuses", "CaseStatus")
    CaseSubStatus = apps.get_model("statuses", "CaseSubStatus")

    SUB_STATUS__UNDER_FINAL_REVIEW__INFORM_LETTER_SENT = "00000000-0000-0000-0000-000000000001"
    SUB_STATUS__FINALISED__REFUSED = "00000000-0000-0000-0000-000000000002"
    SUB_STATUS__FINALISED__APPROVED = "00000000-0000-0000-0000-000000000003"
    SUB_STATUS__FINALISED__APPEAL_REJECTED = "00000000-0000-0000-0000-000000000004"
    SUB_STATUS__FINALISED__APPEAL_REFUSED = "00000000-0000-0000-0000-000000000005"
    SUB_STATUS__FINALISED__APPEAL_APPROVED = "00000000-0000-0000-0000-000000000006"
    SUB_STATUS__UNDER_APPEAL__REQUEST_RECEIVED = "00000000-0000-0000-0000-000000000007"
    SUB_STATUS__UNDER_APPEAL__SENIOR_MANAGER_INSTRUCTIONS = "00000000-0000-0000-0000-000000000008"
    SUB_STATUS__UNDER_APPEAL__PRE_CIRCULATION = "00000000-0000-0000-0000-000000000009"
    SUB_STATUS__UNDER_APPEAL__OGD_ADVICE = "00000000-0000-0000-0000-000000000010"
    SUB_STATUS__UNDER_APPEAL__FINAL_DECISION = "00000000-0000-0000-0000-000000000011"

    CASE_STATUS_UNDER_FINAL_REVIEW = CaseStatus.objects.get(status="under_final_review").id
    CASE_STATUS_FINALISED = CaseStatus.objects.get(status="finalised").id
    CASE_STATUS_UNDER_APPEAL = CaseStatus.objects.get(status="under_appeal").id

    sub_statuses = [
        {
            "id": SUB_STATUS__UNDER_FINAL_REVIEW__INFORM_LETTER_SENT,
            "name": "Inform letter sent",
            "parent_status_id": CASE_STATUS_UNDER_FINAL_REVIEW,
        },
        {
            "id": SUB_STATUS__FINALISED__REFUSED,
            "name": "Refused",
            "parent_status_id": CASE_STATUS_FINALISED,
        },
        {
            "id": SUB_STATUS__FINALISED__APPROVED,
            "name": "Approved",
            "parent_status_id": CASE_STATUS_FINALISED,
        },
        {
            "id": SUB_STATUS__FINALISED__APPEAL_REJECTED,
            "name": "Appeal rejected",
            "parent_status_id": CASE_STATUS_FINALISED,
        },
        {
            "id": SUB_STATUS__FINALISED__APPEAL_REFUSED,
            "name": "Refused after appeal",
            "parent_status_id": CASE_STATUS_FINALISED,
        },
        {
            "id": SUB_STATUS__FINALISED__APPEAL_APPROVED,
            "name": "Approved after appeal",
            "parent_status_id": CASE_STATUS_FINALISED,
        },
        {
            "id": SUB_STATUS__UNDER_APPEAL__REQUEST_RECEIVED,
            "name": "Request received",
            "parent_status_id": CASE_STATUS_UNDER_APPEAL,
        },
        {
            "id": SUB_STATUS__UNDER_APPEAL__SENIOR_MANAGER_INSTRUCTIONS,
            "name": "Senior manager instructions",
            "parent_status_id": CASE_STATUS_UNDER_APPEAL,
        },
        {
            "id": SUB_STATUS__UNDER_APPEAL__PRE_CIRCULATION,
            "name": "Pre-circulation",
            "parent_status_id": CASE_STATUS_UNDER_APPEAL,
        },
        {
            "id": SUB_STATUS__UNDER_APPEAL__OGD_ADVICE,
            "name": "OGD Advice",
            "parent_status_id": CASE_STATUS_UNDER_APPEAL,
        },
        {
            "id": SUB_STATUS__UNDER_APPEAL__FINAL_DECISION,
            "name": "Final decision",
            "parent_status_id": CASE_STATUS_UNDER_APPEAL,
        },
    ]

    for sub_status in sub_statuses:
        CaseSubStatus.objects.create(
            id=sub_status["id"],
            name=sub_status["name"],
            parent_status_id=sub_status["parent_status_id"],
        )


class Migration(migrations.Migration):
    dependencies = [
        ("statuses", "0006_casesubstatus"),
        ("lite_routing", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_case_sub_status_records, migrations.RunPython.noop),
    ]
