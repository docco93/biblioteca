import re
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from .models import Usuario, Aluno, Titulo, Exemplar, Emprestimo
from django.utils import timezone


class UsuarioCreationForm(UserCreationForm):
    """Formulário de criação de administrador pelo Django Admin.

    Precisa apontar explicitamente para o modelo Usuario, já que os
    formulários padrão do Django (UserCreationForm/UserChangeForm)
    fazem referência ao modelo de usuário base, que possui campos
    (como email) que o Usuario não tem.
    """

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username',)


class UsuarioChangeForm(UserChangeForm):
    """Formulário de edição de administrador pelo Django Admin (ver UsuarioCreationForm)."""

    class Meta(UserChangeForm.Meta):
        model = Usuario
        fields = '__all__'


class LoginForm(AuthenticationForm):
    """Formulário customizado de login (apenas para administradores)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nome de usuário'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Senha'
        })


class AlunoForm(forms.ModelForm):
    """Formulário para cadastro e edição de alunos"""

    class Meta:
        model = Aluno
        fields = ['nome', 'idade', 'genero', 'serie']

        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo do aluno',
                'pattern': '[A-Za-zÀ-ÖØ-öø-ÿ\\s]+',
                'title': 'Digite apenas letras.'
            }),
            'idade': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Idade',
                'min': 0
            }),
            'genero': forms.Select(attrs={
                'class': 'form-control'
            }),
            'serie': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def clean_nome(self):
        nome = self.cleaned_data.get('nome', '')
        if not re.match(r'^[A-Za-zÀ-ÖØ-öø-ÿ\s]+$', nome):
            raise ValidationError('O nome deve conter apenas letras.')
        return nome


class TituloForm(forms.ModelForm):
    """Formulário para cadastro e edição de títulos"""
    
    class Meta:
        model = Titulo
        fields = ['lombada', 'autor', 'titulo_da_obra', 'titulo_original', 
                 'subtitulo', 'edicao', 'editora', 'ano_publicacao']
        
        widgets = {
            'lombada': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código da lombada'
            }),
            'autor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do autor'
            }),
            'titulo_da_obra': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título da obra'
            }),
            'titulo_original': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título original (opcional)'
            }),
            'subtitulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Subtítulo (opcional)'
            }),
            'edicao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Edição (opcional)'
            }),
            'editora': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da editora'
            }),
            'ano_publicacao': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '2024'
            }),
        }
    
    def clean_lombada(self):
        lombada = self.cleaned_data.get('lombada')
        if self.instance.pk:
            # Edição - verificar se não existe outro com a mesma lombada
            if Titulo.objects.filter(lombada=lombada).exclude(pk=self.instance.pk).exists():
                raise ValidationError("Já existe um título com esta lombada.")
        else:
            # Criação - verificar se não existe
            if Titulo.objects.filter(lombada=lombada).exists():
                raise ValidationError("Já existe um título com esta lombada.")
        return lombada


class ExemplarForm(forms.ModelForm):
    """Formulário para cadastro e edição de exemplares"""
    
    class Meta:
        model = Exemplar
        fields = ['titulo', 'data_aquisicao']
        
        widgets = {
            'titulo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'data_aquisicao': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }


class EmprestimoForm(forms.ModelForm):
    """Formulário para realizar empréstimos"""
    
    class Meta:
        model = Emprestimo
        fields = ['aluno', 'exemplar', 'data_emprestimo', 'previsao_devolucao', 'observacoes']
        
        widgets = {
            'aluno': forms.Select(attrs={
                'class': 'form-control'
            }),
            'exemplar': forms.Select(attrs={
                'class': 'form-control'
            }),
            'data_emprestimo': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'previsao_devolucao': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações (opcional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Todos os alunos cadastrados (a validação de suspensão/limite é feita em clean_aluno)
        self.fields['aluno'].queryset = Aluno.objects.all().order_by('nome')

        # Filtrar apenas exemplares disponíveis
        self.fields['exemplar'].queryset = Exemplar.objects.filter(disponivel=True)
    
    def clean_aluno(self):
        aluno = self.cleaned_data.get('aluno')
        if aluno and not aluno.pode_emprestar():
            if aluno.esta_suspenso():
                if aluno.data_suspensao and aluno.data_suspensao >= timezone.now().date():
                    mensagem = f"Aluno suspenso até {aluno.data_suspensao.strftime('%d/%m/%Y')}"
                elif aluno.tem_emprestimo_atrasado():
                    mensagem = "Aluno suspenso por ter empréstimos atrasados"
                else:
                    mensagem = "Aluno está suspenso"
                raise ValidationError(mensagem)
            else:
                raise ValidationError("Aluno já possui 3 livros emprestados (limite máximo)")
        return aluno
    
    def clean_exemplar(self):
        exemplar = self.cleaned_data.get('exemplar')
        if exemplar and not exemplar.disponivel:
            raise ValidationError("Este exemplar não está disponível para empréstimo")
        return exemplar


class BuscaAcervoForm(forms.Form):
    """Formulário para busca no acervo"""
    
    OPCOES_BUSCA = [
        ('titulo', 'Título'),
        ('autor', 'Autor'),
        ('todos', 'Título e Autor'),
    ]
    
    termo_busca = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua busca...'
        })
    )
    
    tipo_busca = forms.ChoiceField(
        choices=OPCOES_BUSCA,
        initial='todos',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    editora = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filtrar por editora...'
        })
    )
    
    ano_inicio = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ano inicial'
        })
    )
    
    ano_fim = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ano final'
        })
    )


class DevolucaoForm(forms.Form):
    """Formulário para devolução de livros"""
    
    codigo_exemplar = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Código do exemplar ou escaneie o QR Code'
        })
    )
    
    observacoes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observações sobre a devolução (opcional)'
        })
    )
    
    def clean_codigo_exemplar(self):
        codigo = self.cleaned_data.get('codigo_exemplar')
        try:
            exemplar = Exemplar.objects.get(codigo_exemplar=codigo)
            if not exemplar.esta_emprestado():
                raise ValidationError("Este exemplar não está emprestado")
            return codigo
        except Exemplar.DoesNotExist:
            raise ValidationError("Exemplar não encontrado")
