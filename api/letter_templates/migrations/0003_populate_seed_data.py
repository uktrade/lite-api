# Generated by Django 3.2.11 on 2023-05-22 15:57

from django.db import migrations
from api.cases.enums import AdviceType, CaseTypeEnum

from api.picklists.enums import PickListStatus, PicklistType
from api.teams.enums import TeamIdEnum




def populate_static_data(apps, schema_editor):

    # Create the template 
    Decision = apps.get_model("decisions", "Decision")
    for name, id in AdviceType.ids.items():
        Decision.objects.get_or_create(id=id, name=name)
        
                

class Migration(migrations.Migration):

    dependencies = [
        ("letter_templates", "0002_auto_20210426_1014"),
    ]

    operations = [
        migrations.RunPython(populate_static_data, migrations.RunPython.noop),
    ]