# Generated by Django 2.2.9 on 2020-02-10 13:26

import api.applications.models
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("applications", "0001_initial"),
        ("cases", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="BaseApplication",
            fields=[
                (
                    "case_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="cases.Case",
                    ),
                ),
                ("name", models.TextField(blank=True, default=None, null=True)),
                (
                    "application_type",
                    models.CharField(
                        choices=[
                            ("standard_licence", "Standard Licence"),
                            ("open_licence", "Open Licence"),
                            ("hmrc_query", "HMRC Query"),
                            ("exhibition_clearance", "MOD Exhibition Clearance"),
                        ],
                        default=None,
                        max_length=50,
                    ),
                ),
                ("activity", models.TextField(blank=True, default=None, null=True)),
                ("usage", models.TextField(blank=True, default=None, null=True)),
                (
                    "licence_duration",
                    models.IntegerField(default=None, help_text="Set when application finalised", null=True),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=(api.applications.models.ApplicationPartyMixin, "cases.case"),
        ),
        migrations.CreateModel(
            name="CountryOnApplication",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name="ExternalLocationOnApplication",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name="GoodOnApplication",
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
                ("quantity", models.FloatField(blank=True, default=None, null=True)),
                (
                    "unit",
                    models.CharField(
                        choices=[
                            ("GRM", "Gram(s)"),
                            ("KGM", "Kilogram(s)"),
                            ("NAR", "Number of articles"),
                            ("MTK", "Square metre(s)"),
                            ("MTR", "Metre(s)"),
                            ("LTR", "Litre(s)"),
                            ("MTQ", "Cubic metre(s)"),
                        ],
                        default="GRM",
                        max_length=50,
                    ),
                ),
                ("value", models.DecimalField(decimal_places=2, max_digits=256)),
                ("is_good_incorporated", models.BooleanField(default=False)),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="PartyOnApplication",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
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
                ("deleted_at", models.DateTimeField(default=None, null=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ExhibitionClearanceApplication",
            fields=[
                (
                    "baseapplication_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="applications.BaseApplication",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("applications.baseapplication",),
        ),
        migrations.CreateModel(
            name="HmrcQuery",
            fields=[
                (
                    "baseapplication_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="applications.BaseApplication",
                    ),
                ),
                ("reasoning", models.CharField(blank=True, default=None, max_length=1000, null=True)),
                ("have_goods_departed", models.BooleanField(default=False)),
            ],
            options={
                "abstract": False,
            },
            bases=("applications.baseapplication",),
        ),
        migrations.CreateModel(
            name="OpenApplication",
            fields=[
                (
                    "baseapplication_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="applications.BaseApplication",
                    ),
                ),
                (
                    "export_type",
                    models.CharField(
                        choices=[("permanent", "Permanent"), ("temporary", "Temporary")], default=None, max_length=50
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("applications.baseapplication",),
        ),
        migrations.CreateModel(
            name="StandardApplication",
            fields=[
                (
                    "baseapplication_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="applications.BaseApplication",
                    ),
                ),
                (
                    "export_type",
                    models.CharField(
                        choices=[("permanent", "Permanent"), ("temporary", "Temporary")], default=None, max_length=50
                    ),
                ),
                ("reference_number_on_information_form", models.TextField(blank=True, null=True)),
                (
                    "have_you_been_informed",
                    models.CharField(choices=[("yes", "Yes"), ("no", "No")], default=None, max_length=50),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("applications.baseapplication",),
        ),
        migrations.CreateModel(
            name="SiteOnApplication",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="application_sites",
                        to="applications.BaseApplication",
                    ),
                ),
            ],
        ),
    ]
