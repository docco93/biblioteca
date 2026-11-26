from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('biblioteca', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='titulo',
            name='local_publicacao',
        ),
        migrations.RemoveField(
            model_name='titulo',
            name='isbn',
        ),
        migrations.RemoveField(
            model_name='titulo',
            name='cdu',
        ),
        migrations.RemoveField(
            model_name='titulo',
            name='cutter',
        ),
    ]
