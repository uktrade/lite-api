# Generated by Django 4.2.16 on 2024-11-18 13:14

from django.db import migrations, models, transaction
from django.db.models import Count
import django.db.models.deletion


@transaction.atomic
def populate_previous_decisions(apps, schema_editor):
    Case = apps.get_model("cases", "Case")
    LicenceDecision = apps.get_model("cases", "LicenceDecision")

    licence_decisions_to_update = []

    # We only need to update cases where there are multiple decisions
    # In case of single decision then previous_decision field of licence decision is
    # not set by default so nothing to update
    case_qs = (
        Case.objects.all()
        .annotate(
            num_decisions=Count("licence_decisions"),
        )
        .filter(
            num_decisions__gt=1,
        )
    )

    # By default previous_decision is not set for all decisions.
    # Previous_decision is reset whenever there is a change in decision otherwise it
    # points to the decision in previous instance.
    #
    # When exporting we just filter all decisions where previous_decision is None which
    # gives us the earliest decision time as required
    # ---------------------------------------------------
    #  [ld1, ld2, ..., ldn]       | [previous_decision field value]
    # ---------------------------------------------------
    #  [ISSUED, ISSUED]           | [None, ld1]
    #  [ISSUED, ISSUED, ISSUED]   | [None, ld1, ld2]
    #  [ISSUED, REFUSED]          | [None, None]
    #  [REFUSED, ISSUED]          | [None, None]
    #  [ISSUED, REVOKED]          | [None, None]
    #  [ISSUED, REVOKED, ISSUED]  | [None, None, None]
    # ---------------------------------------------------
    #
    for case in case_qs:
        previous_decision = None
        for item in case.licence_decisions.order_by("created_at"):
            if previous_decision and item.decision == previous_decision.decision:
                item.previous_decision = previous_decision
                licence_decisions_to_update.append(item)

            previous_decision = item

    LicenceDecision.objects.bulk_update(licence_decisions_to_update, ["previous_decision"])


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0070_attach_licence_to_licence_decision"),
    ]

    operations = [
        migrations.AddField(
            model_name="licencedecision",
            name="previous_decision",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="previous_decisions",
                to="cases.licencedecision",
            ),
        ),
        migrations.RunPython(
            populate_previous_decisions,
            migrations.RunPython.noop,
        ),
    ]
