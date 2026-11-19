from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inspections', '0010_samplingresult_incremento_aplicado_and_more'),
    ]

    operations = [
        migrations.RunPython(migrations.RunPython.noop),
    ]
