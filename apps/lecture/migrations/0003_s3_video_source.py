from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("lecture", "0002_alter_lecture_status")]

    operations = [
        migrations.AlterField(
            model_name="lecture",
            name="source",
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
    ]
