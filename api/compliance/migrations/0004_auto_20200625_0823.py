# Generated by Django 2.2.13 on 2020-06-25 08:23

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("compliance", "0003_complianceperson_compliancevisitcase"),
    ]

    operations = [
        migrations.AlterField(
            model_name="complianceperson",
            name="id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="complianceperson",
            name="visit_case",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="people_present",
                to="compliance.ComplianceVisitCase",
            ),
        ),
        migrations.AlterField(
            model_name="compliancevisitcase",
            name="compliance_overview",
            field=models.TextField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name="compliancevisitcase",
            name="compliance_risk_value",
            field=models.CharField(
                choices=[
                    ("very_low", "Very low risk"),
                    ("lower", "Lower risk"),
                    ("medium", "Medium risk"),
                    ("higher", "Higher risk"),
                    ("highest", "Highest risk"),
                ],
                default=None,
                max_length=10,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="compliancevisitcase",
            name="individuals_overview",
            field=models.TextField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name="compliancevisitcase",
            name="individuals_risk_value",
            field=models.CharField(
                choices=[
                    ("very_low", "Very low risk"),
                    ("lower", "Lower risk"),
                    ("medium", "Medium risk"),
                    ("higher", "Higher risk"),
                    ("highest", "Highest risk"),
                ],
                default=None,
                max_length=10,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="compliancevisitcase", name="inspection", field=models.TextField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name="compliancevisitcase", name="overview", field=models.TextField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name="compliancevisitcase", name="products_overview", field=models.TextField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name="compliancevisitcase",
            name="products_risk_value",
            field=models.CharField(
                choices=[
                    ("very_low", "Very low risk"),
                    ("lower", "Lower risk"),
                    ("medium", "Medium risk"),
                    ("higher", "Higher risk"),
                    ("highest", "Highest risk"),
                ],
                default=None,
                max_length=10,
                null=True,
            ),
        ),
    ]
