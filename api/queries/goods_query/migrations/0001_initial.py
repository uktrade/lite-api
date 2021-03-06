# Generated by Django 2.2.9 on 2020-02-10 13:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("queries", "0001_initial"),
        ("goods", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="GoodsQuery",
            fields=[
                (
                    "query_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="queries.Query",
                    ),
                ),
                ("clc_raised_reasons", models.TextField(blank=True, default=None, max_length=2000, null=True)),
                ("pv_grading_raised_reasons", models.TextField(blank=True, default=None, max_length=2000, null=True)),
                ("clc_responded", models.BooleanField(default=None, null=True)),
                ("pv_grading_responded", models.BooleanField(default=None, null=True)),
                (
                    "good",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING, related_name="good", to="goods.Good"
                    ),
                ),
            ],
            options={"abstract": False,},
            bases=("queries.query",),
        ),
    ]
