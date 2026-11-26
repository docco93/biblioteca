from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta
import qrcode
from io import BytesIO
from django.core.files import File
import uuid
import os


class UsuarioManager(BaseUserManager):
    """Gerenciador próprio para o Usuario, já que o UserManager padrão do
    Django tem o campo "email" fixo no código-fonte dele (não olha pra
    REQUIRED_FIELDS) e quebraria ao criar usuário/superusuário, pois o
    modelo Usuario não possui esse campo."""

    use_in_migrations = True

    def _create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError('É necessário informar um nome de usuário.')
        username = self.model.normalize_username(username)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(username, password, **extra_fields)


class Usuario(AbstractUser):
    """Modelo de usuário administrador do sistema (login e senha).

    Alunos NÃO usam este modelo - veja o modelo Aluno abaixo.
    Este modelo serve apenas para os administradores que operam o
    empréstimo/devolução de livros. Não possui e-mail nem recuperação
    de senha por e-mail - a senha é redefinida diretamente pelo Django Admin.
    """
    email = None
    # AbstractUser normalmente exige e-mail ao criar superusuário; como o
    # campo foi removido acima, é preciso limpar essa exigência também.
    REQUIRED_FIELDS = []

    objects = UsuarioManager()

    is_administrador = models.BooleanField(
        default=True,
        help_text='Designa se o usuário tem privilégios de administrador'
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username


class Aluno(models.Model):
    """Modelo para representar um aluno cadastrado na biblioteca.

    O aluno não faz login no sistema - ele é apenas um cadastro
    (nome, idade, gênero, série) usado pelo administrador para
    vincular empréstimos.
    """

    GENERO_MASCULINO = 'M'
    GENERO_FEMININO = 'F'
    GENERO_OUTRO = 'O'
    GENERO_CHOICES = [
        (GENERO_MASCULINO, 'Masculino'),
        (GENERO_FEMININO, 'Feminino'),
        (GENERO_OUTRO, 'Outro'),
    ]

    SERIE_CHOICES = [
        ('Infantil 4', 'Infantil 4'),
        ('Infantil 5', 'Infantil 5'),
        ('1º ano', '1º ano'),
        ('2º ano', '2º ano'),
        ('3º ano', '3º ano'),
        ('4º ano', '4º ano'),
        ('5º ano', '5º ano'),
    ]

    validador_nome = RegexValidator(
        regex=r'^[A-Za-zÀ-ÖØ-öø-ÿ\s]+$',
        message='O nome deve conter apenas letras.'
    )

    nome = models.CharField(max_length=200, validators=[validador_nome])
    idade = models.PositiveIntegerField()
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES)
    serie = models.CharField(
        max_length=50,
        choices=SERIE_CHOICES,
        help_text='Série/turma do aluno'
    )
    data_suspensao = models.DateField(
        null=True,
        blank=True,
        help_text='Data até quando o aluno está suspenso'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Aluno'
        verbose_name_plural = 'Alunos'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.serie})"

    def esta_suspenso(self):
        """Verifica se o aluno está suspenso, seja por data de suspensão ou por atraso"""
        if self.data_suspensao and timezone.now().date() <= self.data_suspensao:
            return True
        if self.tem_emprestimo_atrasado():
            return True
        return False

    def pode_emprestar(self):
        """Verifica se o aluno pode fazer empréstimos"""
        if self.esta_suspenso():
            return False

        # Verifica se tem menos de 3 livros emprestados
        emprestimos_ativos = Emprestimo.objects.filter(
            aluno=self,
            data_devolucao__isnull=True
        ).count()

        # Verifica se há empréstimos atrasados
        if self.tem_emprestimo_atrasado():
            return False

        return emprestimos_ativos < 3

    def livros_emprestados_count(self):
        """Retorna a quantidade de livros atualmente emprestados"""
        return Emprestimo.objects.filter(
            aluno=self,
            data_devolucao__isnull=True
        ).count()

    def suspender(self, dias=30):
        """Suspende o aluno por um número específico de dias"""
        self.data_suspensao = timezone.now().date() + timedelta(days=dias)
        self.save()

    def reativar(self):
        """Remove a suspensão do aluno"""
        self.data_suspensao = None
        self.save()

    def tem_emprestimo_atrasado(self):
        """Verifica se o aluno tem algum empréstimo atrasado"""
        return Emprestimo.objects.filter(
            aluno=self,
            data_devolucao__isnull=True,
            previsao_devolucao__lt=timezone.now().date()
        ).exists()


class Titulo(models.Model):
    """Modelo para representar uma obra/título"""
    lombada = models.CharField(max_length=50, unique=True)
    autor = models.CharField(max_length=200)
    titulo_da_obra = models.CharField(max_length=300)
    titulo_original = models.CharField(max_length=300, blank=True)
    subtitulo = models.CharField(max_length=300, blank=True)
    edicao = models.CharField(max_length=50, blank=True)
    editora = models.CharField(max_length=200)
    ano_publicacao = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Título'
        verbose_name_plural = 'Títulos'
        ordering = ['titulo_da_obra']
    
    def __str__(self):
        return f"{self.titulo_da_obra} - {self.autor}"
    
    def exemplares_disponiveis(self):
        """Retorna a quantidade de exemplares disponíveis"""
        return self.exemplares.filter(disponivel=True).count()
    
    def total_exemplares(self):
        """Retorna o total de exemplares"""
        return self.exemplares.count()


class Exemplar(models.Model):
    """Modelo para representar um exemplar físico de um título"""
    titulo = models.ForeignKey(
        Titulo,
        on_delete=models.CASCADE,
        related_name='exemplares'
    )
    data_aquisicao = models.DateField()
    qr_code = models.ImageField(
        upload_to='qrcodes/',
        blank=True,
        help_text='QR Code gerado automaticamente'
    )
    disponivel = models.BooleanField(default=True)
    codigo_exemplar = models.CharField(
        max_length=50,
        unique=True,
        help_text='Código único do exemplar',
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Exemplar'
        verbose_name_plural = 'Exemplares'
        ordering = ['titulo__titulo_da_obra', 'codigo_exemplar']
    
    def __str__(self):
        return f"{self.titulo.titulo_da_obra} - Exemplar {self.codigo_exemplar}"
    
    def save(self, *args, **kwargs):
        # Verifica se o código ainda não foi gerado e se tem um título associado
        if not self.codigo_exemplar and self.titulo_id:
            # Conta o número de exemplares já associados a esse título específico
            total_exemplares_existentes = Exemplar.objects.filter(titulo=self.titulo).count()
            numero_sequencial = total_exemplares_existentes + 1
            
            # Formata a lombada e o número do exemplar
            lombada = self.titulo.lombada if self.titulo.lombada else "SL"
            self.codigo_exemplar = f"{lombada}-{numero_sequencial:02d}"
            
        # Salvar primeiro para ter um ID
        super().save(*args, **kwargs)
        
        # Gerar QR Code após salvar se não existir
        if not self.qr_code:
            self.gerar_qr_code()
    
    def gerar_qr_code(self):
        """Gera QR Code para o exemplar"""
        try:
            # URL que será codificada no QR Code
            qr_data = f"http://localhost:8000/exemplar/{self.id}/"
            
            # Criar QR Code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Criar imagem
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Salvar em buffer
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Nome do arquivo
            filename = f'qr_exemplar_{self.id}.png'
            
            # Salvar no campo
            self.qr_code.save(
                filename,
                File(buffer, name=filename),
                save=False  # Evitar recursão
            )
            
            # Salvar apenas o campo qr_code
            super().save(update_fields=['qr_code'])
            
            buffer.close()
            
        except Exception as e:
            print(f"Erro ao gerar QR Code para exemplar {self.id}: {e}")
    
    def esta_emprestado(self):
        """Verifica se o exemplar está emprestado"""
        return Emprestimo.objects.filter(
            exemplar=self,
            data_devolucao__isnull=True
        ).exists()
    
    def emprestimo_atual(self):
        """Retorna o empréstimo atual se existir"""
        try:
            return Emprestimo.objects.get(
                exemplar=self,
                data_devolucao__isnull=True
            )
        except Emprestimo.DoesNotExist:
            return None


class Emprestimo(models.Model):
    """Modelo para representar um empréstimo"""
    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE,
        related_name='emprestimos'
    )
    exemplar = models.ForeignKey(
        Exemplar,
        on_delete=models.CASCADE,
        related_name='emprestimos'
    )
    data_emprestimo = models.DateTimeField(default=timezone.now)
    previsao_devolucao = models.DateField()
    data_devolucao = models.DateTimeField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Empréstimo'
        verbose_name_plural = 'Empréstimos'
        ordering = ['-data_emprestimo']
    
    def __str__(self):
        status = "Devolvido" if self.data_devolucao else "Em andamento"
        return f"{self.aluno.nome} - {self.exemplar.titulo.titulo_da_obra} ({status})"
    
    def save(self, *args, **kwargs):
        # Definir previsão de devolução (1 mês) se não definida
        if not self.previsao_devolucao:
            self.previsao_devolucao = (timezone.now() + timedelta(days=30)).date()
        
        # Atualizar disponibilidade do exemplar
        if not self.data_devolucao:  # Empréstimo ativo
            self.exemplar.disponivel = False
        else:  # Devolução
            self.exemplar.disponivel = True
        
        self.exemplar.save()
        super().save(*args, **kwargs)
    
    def esta_atrasado(self):
        """Verifica se o empréstimo está atrasado"""
        if self.data_devolucao:  # Já foi devolvido
            return False
        return timezone.now().date() > self.previsao_devolucao
    
    def dias_atraso(self):
        """Calcula quantos dias de atraso"""
        if not self.esta_atrasado():
            return 0
        return (timezone.now().date() - self.previsao_devolucao).days
    
    def devolver(self):
        """Realiza a devolução do livro"""
        if not self.data_devolucao:
            self.exemplar.disponivel = True
            self.exemplar.save()
            
            # Aplicar suspensão se houver atraso
            if self.esta_atrasado():
                dias_atraso = self.dias_atraso()
                data_suspensao = timezone.now().date() + timedelta(days=dias_atraso)
                
                # Atualizar ou definir suspensão
                if self.aluno.data_suspensao:
                    if data_suspensao > self.aluno.data_suspensao:
                        self.aluno.data_suspensao = data_suspensao
                else:
                    self.aluno.data_suspensao = data_suspensao
                
                self.aluno.save()
            self.data_devolucao = timezone.now()
            self.save()
    
    def dias_para_vencimento(self):
        """Calcula quantos dias faltam para o vencimento"""
        if self.data_devolucao:
            return None
        
        diferenca = self.previsao_devolucao - timezone.now().date()
        return diferenca.days


class HistoricoEmprestimo(models.Model):
    """Modelo para manter histórico detalhado de empréstimos"""
    emprestimo = models.OneToOneField(
        Emprestimo,
        on_delete=models.CASCADE,
        related_name='historico'
    )
    renovacoes = models.IntegerField(default=0)
    notificacoes_enviadas = models.IntegerField(default=0)
    ultima_notificacao = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Histórico de Empréstimo'
        verbose_name_plural = 'Históricos de Empréstimos'
    
    def __str__(self):
        return f"Histórico - {self.emprestimo}"