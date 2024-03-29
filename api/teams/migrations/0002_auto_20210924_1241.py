# Generated by Django 3.1.12 on 2021-09-24 11:41

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("teams", "0001_squashed_0003_auto_20210325_0812"),
    ]

    operations = [
        migrations.CreateModel(
            name="Department",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.TextField(unique=True)),
            ],
        ),
        migrations.AddField(
            model_name="team",
            name="department",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="teams",
                to="teams.department",
            ),
        ),
    ]
