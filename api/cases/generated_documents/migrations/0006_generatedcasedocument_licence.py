# Generated by Django 2.2.13 on 2020-07-02 13:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("licences", "0006_licence_sent_at"),
        ("generated_documents", "0005_generatedcasedocument_advice_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="generatedcasedocument",
            name="licence",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to="licences.Licence"),
        ),
    ]
