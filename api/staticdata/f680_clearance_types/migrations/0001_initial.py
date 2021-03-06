# Generated by Django 2.2.10 on 2020-02-28 14:53

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="F680ClearanceType",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "name",
                    models.CharField(
                        choices=[
                            ("market_survey", "Market Survey"),
                            ("initial_discussions_and_promotions", "Initial discussions and promotions"),
                            ("demonstration_uk_overseas_customers", "Demonstration in the UK to overseas customers"),
                            ("demonstration_overseas", "Demonstration overseas"),
                            ("training", "Training"),
                            ("through_life_support", "Through life support"),
                        ],
                        max_length=45,
                    ),
                ),
            ],
        ),
    ]
