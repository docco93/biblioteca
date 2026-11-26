from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from biblioteca.models import Aluno, Titulo, Exemplar, Emprestimo
from datetime import date, timedelta
import random

Usuario = get_user_model()

class Command(BaseCommand):
    help = 'Popula o banco de dados com dados de exemplo'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando população do banco de dados...')

        # Criar usuário administrador
        if not Usuario.objects.filter(username='admin').exists():
            admin = Usuario.objects.create_user(
                username='admin',
                password='admin123',
                first_name='Administrador',
                last_name='Sistema',
                is_administrador=True,
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(f'✓ Usuário administrador criado: {admin.username}')

        # Criar alguns alunos de exemplo
        alunos_dados = [
            {'nome': 'João Silva', 'idade': 9, 'genero': 'M', 'serie': '4º ano'},
            {'nome': 'Maria Santos', 'idade': 10, 'genero': 'F', 'serie': '5º ano'},
            {'nome': 'Pedro Costa', 'idade': 8, 'genero': 'M', 'serie': '3º ano'},
        ]

        for dados in alunos_dados:
            if not Aluno.objects.filter(nome=dados['nome']).exists():
                aluno = Aluno.objects.create(**dados)
                self.stdout.write(f'✓ Aluno criado: {aluno.nome}')

        # Criar títulos de exemplo
        titulos_dados = [
            {
                'lombada': 'FIC001',
                'autor': 'Machado de Assis',
                'titulo_da_obra': 'Dom Casmurro',
                'editora': 'Ática',
                'ano_publicacao': 2020,
            },
            {
                'lombada': 'FIC002',
                'autor': 'José de Alencar',
                'titulo_da_obra': 'O Guarani',
                'editora': 'Saraiva',
                'ano_publicacao': 2019,
            },
            {
                'lombada': 'TEC001',
                'autor': 'Eric Matthes',
                'titulo_da_obra': 'Curso Intensivo de Python',
                'titulo_original': 'Python Crash Course',
                'editora': 'Novatec',
                'ano_publicacao': 2021,
            },
            {
                'lombada': 'MAT001',
                'autor': 'Howard Anton',
                'titulo_da_obra': 'Cálculo - Volume 1',
                'editora': 'Bookman',
                'ano_publicacao': 2018,
            },
            {
                'lombada': 'HIS001',
                'autor': 'Boris Fausto',
                'titulo_da_obra': 'História do Brasil',
                'editora': 'EDUSP',
                'ano_publicacao': 2019,
            }
        ]

        for dados in titulos_dados:
            if not Titulo.objects.filter(lombada=dados['lombada']).exists():
                titulo = Titulo.objects.create(**dados)
                self.stdout.write(f'✓ Título criado: {titulo.titulo_da_obra}')

                # Criar 2-3 exemplares para cada título
                num_exemplares = random.randint(2, 3)
                for i in range(num_exemplares):
                    exemplar = Exemplar.objects.create(
                        titulo=titulo,
                        data_aquisicao=date.today() - timedelta(days=random.randint(30, 365)),
                        codigo_exemplar=f"{titulo.lombada}-{i+1:03d}"
                    )
                    self.stdout.write(f'  ✓ Exemplar criado: {exemplar.codigo_exemplar}')

        # Criar alguns empréstimos de exemplo
        alunos = Aluno.objects.all()
        exemplares = Exemplar.objects.all()

        if alunos.exists() and exemplares.exists():
            for _ in range(5):  # 5 empréstimos de exemplo
                aluno = random.choice(alunos)
                exemplar = random.choice(exemplares)

                if exemplar.disponivel and aluno.pode_emprestar():
                    emprestimo = Emprestimo.objects.create(
                        aluno=aluno,
                        exemplar=exemplar,
                        previsao_devolucao=date.today() + timedelta(days=30)
                    )
                    self.stdout.write(f'✓ Empréstimo criado: {aluno.nome} - {exemplar.titulo.titulo_da_obra}')

        self.stdout.write(
            self.style.SUCCESS('✅ Banco de dados populado com sucesso!')
        )

        # Mostrar estatísticas
        self.stdout.write('\n📊 Estatísticas:')
        self.stdout.write(f'   Alunos: {Aluno.objects.count()}')
        self.stdout.write(f'   Títulos: {Titulo.objects.count()}')
        self.stdout.write(f'   Exemplares: {Exemplar.objects.count()}')
        self.stdout.write(f'   Empréstimos ativos: {Emprestimo.objects.filter(data_devolucao__isnull=True).count()}')

        self.stdout.write('\n🔑 Credenciais de acesso (administrador):')
        self.stdout.write('   Admin: admin / admin123')
