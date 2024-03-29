# Generated by Django 3.2.16 on 2023-01-10 15:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("statuses", "0004_auto_20210223_1214"),
        ("cases", "0053_auto_20221122_1039"),
        ("routing_rules", "0002_auto_20220824_0925"),
    ]

    operations = [
        migrations.CreateModel(
            name="RoutingHistory",
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
                ("entity_object_id", models.CharField(db_index=True, max_length=255)),
                ("action", models.CharField(choices=[("add", "Add"), ("remove", "Remove")], max_length=10)),
                (
                    "orchestrator_type",
                    models.CharField(
                        choices=[("manual", "Manual"), ("routing_engine", "Routing Engine")], max_length=20
                    ),
                ),
                ("case_flags", models.JSONField()),
                ("case_queues", models.JSONField()),
                ("rule_identifier", models.CharField(blank=True, default="", max_length=256)),
                ("commit_sha", models.CharField(max_length=40)),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="routing_history_records",
                        to="cases.case",
                    ),
                ),
                (
                    "case_status",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, related_name="+", to="statuses.casestatus"
                    ),
                ),
                (
                    "entity_content_type",
                    models.ForeignKey(
                        blank=True,
                        limit_choices_to=models.Q(
                            models.Q(("app_label", "queues"), ("model", "Queue")),
                            models.Q(("app_label", "flags"), ("model", "Flag")),
                            _connector="OR",
                        ),
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="contenttypes.contenttype",
                    ),
                ),
                (
                    "orchestrator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, related_name="+", to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
