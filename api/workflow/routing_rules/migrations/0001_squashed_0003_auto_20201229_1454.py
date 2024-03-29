# Generated by Django 3.1.8 on 2021-04-26 07:46

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import separatedvaluesfield.models
import uuid


class Migration(migrations.Migration):

    replaces = [
        ("routing_rules", "0001_initial"),
        ("routing_rules", "0002_auto_20200408_1023"),
        ("routing_rules", "0003_auto_20201229_1454"),
    ]

    initial = True

    dependencies = [
        ("countries", "0001_initial"),
        ("flags", "0004_auto_20200326_1548"),
        ("users", "0005_auto_20200322_1547"),
        ("cases", "0013_auto_20200325_1544"),
        ("teams", "0002_auto_20200307_1805"),
        ("queues", "0001_initial"),
        ("flags", "0009_auto_20201229_1454"),
        ("statuses", "0003_auto_20200318_1730"),
    ]

    operations = [
        migrations.CreateModel(
            name="RoutingRule",
            fields=[
                (
                    "created_at",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created_at"
                    ),
                ),
                (
                    "updated_at",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="updated_at"
                    ),
                ),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tier", models.PositiveSmallIntegerField()),
                (
                    "additional_rules",
                    separatedvaluesfield.models.SeparatedValuesField(
                        blank=True,
                        choices=[
                            ("users", "Users"),
                            ("case_types", "Case Types"),
                            ("flags", "flags"),
                            ("country", "Country"),
                        ],
                        default=None,
                        max_length=100,
                        null=True,
                    ),
                ),
                ("active", models.BooleanField(default=True)),
                ("case_types", models.ManyToManyField(blank=True, related_name="routing_rules", to="cases.CaseType")),
                (
                    "country",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="routing_rules",
                        to="countries.country",
                    ),
                ),
                ("flags", models.ManyToManyField(blank=True, related_name="routing_rules", to="flags.Flag")),
                (
                    "queue",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING, related_name="routing_rules", to="queues.queue"
                    ),
                ),
                (
                    "status",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="routing_rules",
                        to="statuses.casestatus",
                    ),
                ),
                ("team", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="teams.team")),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="routing_rules",
                        to="users.govuser",
                    ),
                ),
            ],
            options={
                "ordering": ["team__name", "tier", "-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="routingrule",
            index=models.Index(fields=["created_at", "tier"], name="routing_rul_created_70ce43_idx"),
        ),
        migrations.AlterField(
            model_name="routingrule",
            name="team",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="routing_rules", to="teams.team"
            ),
        ),
        migrations.RenameField(
            model_name="routingrule",
            old_name="flags",
            new_name="flags_to_include",
        ),
        migrations.AddField(
            model_name="routingrule",
            name="flags_to_exclude",
            field=models.ManyToManyField(blank=True, related_name="exclude_routing_rules", to="flags.Flag"),
        ),
    ]
