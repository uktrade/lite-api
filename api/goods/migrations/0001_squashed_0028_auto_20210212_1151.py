# Generated by Django 3.1.8 on 2021-04-26 05:57

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.migrations.operations.special
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import uuid


def nullify_is_good_controled(apps, schema_editor):
    Good = apps.get_model("goods", "Good")
    Good.objects.filter(is_good_controlled="unsure").update(is_good_controlled=None)


class Migration(migrations.Migration):

    replaces = [
        ("goods", "0001_initial"),
        ("goods", "0002_gooddocument_organisation"),
        ("goods", "0003_auto_20200210_1326"),
        ("goods", "0004_auto_20200212_1153"),
        ("goods", "0005_auto_20200214_1639"),
        ("goods", "0006_auto_20200226_1218"),
        ("goods", "0007_auto_20200303_1516"),
        ("goods", "0008_auto_20200416_0844"),
        ("goods", "0009_auto_20200416_0859"),
        ("goods", "0010_auto_20200420_1430"),
        ("goods", "0011_auto_20200619_1449"),
        ("goods", "0012_good_software_or_technology_details"),
        ("goods", "0013_auto_20200625_0753"),
        ("goods", "0014_auto_20200702_1113"),
        ("goods", "0015_auto_20200925_1105"),
        ("goods", "0016_firearmgooddetails_serial_number"),
        ("goods", "0017_auto_20201124_1613"),
        ("goods", "0016_auto_20201123_0332"),
        ("goods", "0018_merge_20201127_1102"),
        ("goods", "0019_auto_20201127_1123"),
        ("goods", "0020_auto_20201130_0142"),
        ("goods", "0021_auto_20201130_1614"),
        ("goods", "0022_firearmgooddetails_is_deactivated_to_standard"),
        ("goods", "0021_auto_20201201_1027"),
        ("goods", "0023_merge_20201202_1029"),
        ("goods", "0024_auto_20201204_0309"),
        ("goods", "0025_good_name"),
        ("goods", "0026_auto_20210205_1408"),
        ("goods", "0027_remove_good_missing_document_reason"),
        ("goods", "0028_auto_20210212_1151"),
    ]

    initial = True

    dependencies = [
        ("documents", "0001_initial"),
        ("flags", "0001_initial"),
        ("organisations", "0001_initial"),
        ("users", "0001_initial"),
        ("control_list_entries", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Good",
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
                ("description", models.TextField(max_length=280)),
                (
                    "is_good_controlled",
                    models.CharField(
                        choices=[("yes", "Yes"), ("no", "No"), ("unsure", "I don't know")],
                        default="unsure",
                        max_length=20,
                    ),
                ),
                ("control_code", models.CharField(blank=True, default="", max_length=20, null=True)),
                (
                    "is_pv_graded",
                    models.CharField(
                        choices=[("yes", "Yes"), ("no", "No"), ("grading_required", "Good needs to be graded")],
                        default="grading_required",
                        max_length=20,
                    ),
                ),
                ("part_number", models.CharField(blank=True, default="", max_length=255, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("submitted", "Submitted"),
                            ("query", "Goods Query"),
                            ("verified", "Verified"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                (
                    "missing_document_reason",
                    models.CharField(
                        choices=[
                            ("NO_DOCUMENT", "No document available"),
                            ("OFFICIAL_SENSITIVE", "Document is above OFFICIAL-SENSITIVE"),
                        ],
                        max_length=30,
                        null=True,
                    ),
                ),
                ("comment", models.TextField(blank=True, default=None, max_length=2000, null=True)),
                ("grading_comment", models.TextField(blank=True, default=None, max_length=2000, null=True)),
                ("report_summary", models.TextField(blank=True, default=None, max_length=5000, null=True)),
                ("flags", models.ManyToManyField(related_name="goods", to="flags.Flag")),
                (
                    "organisation",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="organisations.organisation"),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="PvGradingDetails",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "grading",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("uk_unclassified", "UK UNCLASSIFIED"),
                            ("uk_official", "UK OFFICIAL"),
                            ("uk_official_sensitive", "UK OFFICIAL - SENSITIVE"),
                            ("uk_secret", "UK SECRET"),
                            ("uk_top_secret", "UK TOP SECRET"),
                            ("nato_unclassified", "NATO UNCLASSIFIED"),
                            ("nato_confidential", "NATO CONFIDENTIAL"),
                            ("nato_restricted", "NATO RESTRICTED"),
                            ("nato_secret", "NATO SECRET"),
                            ("occar_unclassified", "OCCAR UNCLASSIFIED"),
                            ("occar_confidential", "OCCAR CONFIDENTIAL"),
                            ("occar_restricted", "OCCAR RESTRICTED"),
                            ("occar_secret", "OCCAR SECRET"),
                        ],
                        default=None,
                        max_length=30,
                        null=True,
                    ),
                ),
                ("custom_grading", models.TextField(blank=True, max_length=100, null=True)),
                ("prefix", models.CharField(blank=True, max_length=30, null=True)),
                ("suffix", models.CharField(blank=True, max_length=30, null=True)),
                ("issuing_authority", models.CharField(blank=True, max_length=100, null=True)),
                ("reference", models.CharField(blank=True, max_length=100, null=True)),
                ("date_of_issue", models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="GoodDocument",
            fields=[
                (
                    "document_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="documents.document",
                    ),
                ),
                ("description", models.TextField(blank=True, default=None, max_length=280, null=True)),
                ("good", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="goods.good")),
                (
                    "organisation",
                    models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to="organisations.organisation"),
                ),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to="users.exporteruser")),
            ],
            options={
                "abstract": False,
            },
            bases=("documents.document",),
        ),
        migrations.AddField(
            model_name="good",
            name="pv_grading_details",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="goods.pvgradingdetails",
            ),
        ),
        migrations.AlterField(
            model_name="good",
            name="missing_document_reason",
            field=models.CharField(
                choices=[
                    ("NO_DOCUMENT", "No document available for the product"),
                    ("OFFICIAL_SENSITIVE", "Document is above official-sensitive"),
                ],
                max_length=30,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="good",
            name="missing_document_reason",
            field=models.CharField(
                choices=[
                    ("NO_DOCUMENT", "No document available"),
                    ("OFFICIAL_SENSITIVE", "Document is above OFFICIAL-SENSITIVE"),
                ],
                max_length=30,
                null=True,
            ),
        ),
        migrations.RenameField(
            model_name="good",
            old_name="control_code",
            new_name="control_list_entry",
        ),
        migrations.AlterModelTable(
            name="good",
            table="good",
        ),
        migrations.RemoveField(
            model_name="good",
            name="control_list_entry",
        ),
        migrations.AddField(
            model_name="good",
            name="control_list_entries",
            field=models.ManyToManyField(related_name="goods", to="control_list_entries.ControlListEntry"),
        ),
        migrations.AlterModelOptions(
            name="good",
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddField(
            model_name="good",
            name="component_details",
            field=models.TextField(blank=True, default=None, max_length=2000, null=True),
        ),
        migrations.AddField(
            model_name="good",
            name="information_security_details",
            field=models.TextField(blank=True, default=None, max_length=2000, null=True),
        ),
        migrations.AddField(
            model_name="good",
            name="is_component",
            field=models.CharField(
                choices=[
                    ("yes_designed", "Yes, it's designed specially for hardware"),
                    ("yes_modified", "Yes, it's been modified for hardware"),
                    ("yes_general", "Yes, it's a general purpose component"),
                    ("no", "No"),
                ],
                max_length=15,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="good",
            name="item_category",
            field=models.CharField(
                choices=[
                    ("group1_platform", "Platform, vehicle, system or machine"),
                    ("group1_device", "Device, equipment or object"),
                    ("group1_components", "Components, modules or accessories of something"),
                    ("group1_materials", "Materials or substances"),
                    ("group2_firearms", "Firearms"),
                    ("group3_software", "Software"),
                    ("group3_technology", "Technology"),
                ],
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="good",
            name="modified_military_use_details",
            field=models.TextField(blank=True, default=None, max_length=2000, null=True),
        ),
        migrations.AddField(
            model_name="good",
            name="uses_information_security",
            field=models.BooleanField(default=None, null=True),
        ),
        migrations.AddField(
            model_name="good",
            name="software_or_technology_details",
            field=models.TextField(blank=True, default=None, max_length=2000, null=True),
        ),
        migrations.AddField(
            model_name="good",
            name="is_military_use",
            field=models.CharField(
                choices=[
                    ("yes_designed", "Yes, specially designed for military use"),
                    ("yes_modified", "Yes, modified for military use"),
                    ("no", "No"),
                ],
                max_length=15,
                null=True,
            ),
        ),
        migrations.CreateModel(
            name="FirearmGoodDetails",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("firearms", "Firearms"),
                            ("components_for_firearms", "Components for firearms"),
                            ("ammunition", "Ammunition"),
                            ("components_for_ammunition", "Components for ammunition"),
                        ],
                        max_length=25,
                    ),
                ),
                ("year_of_manufacture", models.PositiveSmallIntegerField()),
                ("calibre", models.TextField(max_length=15)),
                ("is_covered_by_firearm_act_section_one_two_or_five", models.BooleanField()),
                ("section_certificate_number", models.CharField(blank=True, max_length=100, null=True)),
                ("section_certificate_date_of_expiry", models.DateField(blank=True, null=True)),
                ("has_identification_markings", models.BooleanField()),
                ("identification_markings_details", models.TextField(blank=True, max_length=2000, null=True)),
                ("no_identification_markings_details", models.TextField(blank=True, max_length=2000, null=True)),
            ],
        ),
        migrations.AddField(
            model_name="good",
            name="firearm_details",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="goods.firearmgooddetails",
            ),
        ),
        migrations.AlterField(
            model_name="good",
            name="is_good_controlled",
            field=models.CharField(default=None, max_length=20, null=True),
        ),
        migrations.RunPython(
            code=nullify_is_good_controled,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="good",
            name="is_good_controlled",
            field=models.BooleanField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="firearmgooddetails",
            name="serial_number",
            field=models.TextField(default=""),
        ),
        migrations.AddField(
            model_name="firearmgooddetails",
            name="has_proof_mark",
            field=models.BooleanField(
                help_text="Has been proofed (by a proof house) indicating it is safe to be used.", null=True
            ),
        ),
        migrations.AlterField(
            model_name="firearmgooddetails",
            name="type",
            field=models.TextField(
                choices=[
                    ("firearms", "Firearms"),
                    ("components_for_firearms", "Components for firearms"),
                    ("ammunition", "Ammunition"),
                    ("components_for_ammunition", "Components for ammunition"),
                    ("firearms_accessory", "Accessory of a firearm"),
                    ("software_related_to_firearms", "Software relating to a firearm"),
                    ("technology_related_to_firearms", "Technology relating to a firearm"),
                ]
            ),
        ),
        migrations.AlterField(
            model_name="firearmgooddetails",
            name="calibre",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="firearmgooddetails",
            name="year_of_manufacture",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="firearmgooddetails",
            name="no_proof_mark_details",
            field=models.TextField(
                blank=True,
                default="",
                help_text="The reason why `has_proof_mark` is False (which should normally be True).",
            ),
        ),
        migrations.AddField(
            model_name="firearmgooddetails",
            name="is_sporting_shotgun",
            field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name="firearmgooddetails",
            name="has_identification_markings",
            field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name="firearmgooddetails",
            name="is_covered_by_firearm_act_section_one_two_or_five",
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name="firearmgooddetails",
            name="date_of_deactivation",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="firearmgooddetails",
            name="deactivation_standard",
            field=models.TextField(default=""),
        ),
        migrations.AddField(
            model_name="firearmgooddetails",
            name="deactivation_standard_other",
            field=models.TextField(default=""),
        ),
        migrations.AddField(
            model_name="firearmgooddetails",
            name="is_deactivated",
            field=models.BooleanField(help_text="Has the firearms been deactivated?", null=True),
        ),
        migrations.AddField(
            model_name="firearmgooddetails",
            name="is_deactivated_to_standard",
            field=models.BooleanField(help_text="Has the firearms been deactivated to UK/EU standards?", null=True),
        ),
        migrations.AddField(
            model_name="firearmgooddetails",
            name="is_replica",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="firearmgooddetails",
            name="replica_description",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="firearmgooddetails",
            name="firearms_act_section",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="firearmgooddetails",
            name="section_certificate_missing",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="firearmgooddetails",
            name="section_certificate_missing_reason",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="firearmgooddetails",
            name="is_covered_by_firearm_act_section_one_two_or_five",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="good",
            name="name",
            field=models.TextField(default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="good",
            name="is_document_available",
            field=models.BooleanField(default=None, null=True),
        ),
        migrations.AddField(
            model_name="good",
            name="is_document_sensitive",
            field=models.BooleanField(default=None, null=True),
        ),
        migrations.RemoveField(
            model_name="good",
            name="missing_document_reason",
        ),
        migrations.RemoveField(
            model_name="firearmgooddetails",
            name="identification_markings_details",
        ),
        migrations.AddField(
            model_name="firearmgooddetails",
            name="number_of_items",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="firearmgooddetails",
            name="serial_numbers",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.TextField(default=""), default=list, size=None
            ),
        ),
    ]
