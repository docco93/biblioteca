from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('biblioteca', '0002_remove_titulo_local_publicacao_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usuario',
            name='email',
        ),
    ]
