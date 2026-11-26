import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('biblioteca', '0003_remove_usuario_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aluno',
            name='nome',
            field=models.CharField(
                max_length=200,
                validators=[
                    django.core.validators.RegexValidator(
                        regex='^[A-Za-zÀ-ÖØ-öø-ÿ\\s]+$',
                        message='O nome deve conter apenas letras.'
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name='aluno',
            name='serie',
            field=models.CharField(
                choices=[
                    ('Infantil 4', 'Infantil 4'),
                    ('Infantil 5', 'Infantil 5'),
                    ('1º ano', '1º ano'),
                    ('2º ano', '2º ano'),
                    ('3º ano', '3º ano'),
                    ('4º ano', '4º ano'),
                    ('5º ano', '5º ano'),
                ],
                help_text='Série/turma do aluno',
                max_length=50,
            ),
        ),
    ]
