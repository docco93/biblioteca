from django.db import migrations
import biblioteca.models


class Migration(migrations.Migration):

    dependencies = [
        ('biblioteca', '0004_aluno_nome_validator_serie_choices'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='usuario',
            managers=[
                ('objects', biblioteca.models.UsuarioManager()),
            ],
        ),
    ]
