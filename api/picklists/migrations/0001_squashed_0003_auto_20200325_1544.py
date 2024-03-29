# Generated by Django 3.1.8 on 2021-04-23 11:31

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import uuid


class Migration(migrations.Migration):

    replaces = [
        ("picklists", "0001_initial"),
        ("picklists", "0002_auto_20200318_1400"),
        ("picklists", "0003_auto_20200325_1544"),
    ]

    initial = True

    dependencies = [
        ("teams", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PicklistItem",
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
                ("name", models.TextField()),
                ("text", models.TextField(max_length=5000)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("proviso", "Proviso"),
                            ("ecju_query", "Standard ECJU Query"),
                            ("letter_paragraph", "Letter Paragraph"),
                            ("report_summary", "Report Summary"),
                            ("standard_advice", "Standard Advice"),
                            ("footnotes", "Footnotes"),
                            ("pre_visit_questionnaire", "Pre-Visit Questionnaire questions (ECJU Query)"),
                            ("compliance_actions", "Compliance Actions (ECJU Query)"),
                        ],
                        max_length=50,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Active"), ("deactivated", "Deactivated")], default="active", max_length=50
                    ),
                ),
                (
                    "team",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="organisation_team", to="teams.team"
                    ),
                ),
            ],
        ),
    ]
