from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cherry_china_validation', '0004_cherrychinareport_attempts_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cherrychinareport',
            name='pdf_data',
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
    ]