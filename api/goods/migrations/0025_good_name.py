from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("goods", "0024_auto_20201204_0309"),
    ]

    operations = [
        migrations.AddField(
            model_name="good", name="name", field=models.TextField(default=""), preserve_default=False,
        ),
    ]
