from django.db import migrations
from sortedm2m.operations import AlterSortedManyToManyField
import sortedm2m.fields



class Migration(migrations.Migration):

    dependencies = [
        ('letter_templates', '0001_initial'),
    ]

    operations = [
        AlterSortedManyToManyField(
            model_name='lettertemplate',
            name='letter_paragraphs',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, to='picklists.PicklistItem'),
        ),
    ]
