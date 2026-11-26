from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.db.models import Count, Q
from .models import Usuario, Aluno, Titulo, Exemplar, Emprestimo, HistoricoEmprestimo
from .forms import UsuarioCreationForm, UsuarioChangeForm


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Admin customizado para o modelo Usuario (administradores do sistema)"""

    add_form = UsuarioCreationForm
    form = UsuarioChangeForm

    list_display = ('username', 'first_name', 'last_name',
                   'is_administrador', 'is_active', 'is_staff')

    list_filter = ('is_administrador', 'is_active', 'is_staff')

    search_fields = ('username', 'first_name', 'last_name')

    ordering = ('first_name', 'last_name')

    list_editable = ('is_administrador',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name')}),
        ('Permissões', {
            'fields': ('is_administrador', 'is_active', 'is_staff', 'is_superuser',
                      'groups', 'user_permissions'),
        }),
        ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2',
                      'first_name', 'last_name', 'is_administrador'),
        }),
    )


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    """Admin para o modelo Aluno"""

    list_display = ('nome', 'idade', 'genero', 'serie',
                   'esta_suspenso_display', 'livros_emprestados_count')

    list_filter = ('genero', 'serie', 'data_suspensao')

    search_fields = ('nome', 'serie')

    ordering = ('nome',)

    fieldsets = (
        ('Dados do Aluno', {
            'fields': ('nome', 'idade', 'genero', 'serie')
        }),
        ('Situação', {
            'fields': ('data_suspensao',)
        }),
    )

    def esta_suspenso_display(self, obj):
        """Exibe status de suspensão com cores"""
        if obj.esta_suspenso():
            return format_html(
                '<span style="color: red; font-weight: bold;">Suspenso até {}</span>',
                obj.data_suspensao.strftime('%d/%m/%Y')
            )
        return format_html('<span style="color: green;">Ativo</span>')

    esta_suspenso_display.short_description = 'Status'


@admin.register(Titulo)
class TituloAdmin(admin.ModelAdmin):
    """Admin para o modelo Titulo"""
    
    list_display = ('lombada', 'titulo_da_obra', 'autor', 'editora', 
                   'ano_publicacao', 'exemplares_disponiveis_admin', 'total_exemplares_admin')
    
    list_filter = ('editora', 'ano_publicacao')
    
    search_fields = ('titulo_da_obra', 'autor', 'lombada')
    
    ordering = ('titulo_da_obra',)
    
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('lombada', 'titulo_da_obra', 'titulo_original', 'subtitulo', 'autor')
        }),
        ('Publicação', {
            'fields': ('editora', 'edicao', 'ano_publicacao')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Anota a contagem de exemplares para permitir ordenação pelas colunas"""
        qs = super().get_queryset(request)
        qs = qs.annotate(
            _total_exemplares=Count('exemplares', distinct=True),
            _exemplares_disponiveis=Count(
                'exemplares',
                filter=Q(exemplares__disponivel=True),
                distinct=True
            ),
        )
        return qs

    @admin.display(description='Exemplares Disponíveis', ordering='_exemplares_disponiveis')
    def exemplares_disponiveis_admin(self, obj):
        return obj._exemplares_disponiveis

    @admin.display(description='Total Exemplares', ordering='_total_exemplares')
    def total_exemplares_admin(self, obj):
        return obj._total_exemplares

    def changelist_view(self, request, extra_context=None):
        """Adiciona o total geral de exemplares disponíveis e cadastrados
        (considerando os títulos atualmente exibidos, com filtros/busca aplicados)"""
        response = super().changelist_view(request, extra_context=extra_context)

        try:
            titulo_ids = list(response.context_data['cl'].queryset.values_list('id', flat=True))
        except (AttributeError, KeyError):
            return response

        totais = Exemplar.objects.filter(titulo_id__in=titulo_ids).aggregate(
            total_exemplares_geral=Count('id'),
            total_disponiveis_geral=Count('id', filter=Q(disponivel=True)),
        )

        response.context_data['total_exemplares_geral'] = totais['total_exemplares_geral'] or 0
        response.context_data['total_disponiveis_geral'] = totais['total_disponiveis_geral'] or 0

        return response


@admin.register(Exemplar)
class ExemplarAdmin(admin.ModelAdmin):
    """Admin para o modelo Exemplar"""
    
    list_display = ('codigo_exemplar', 'titulo', 'data_aquisicao', 
                   'disponivel', 'esta_emprestado_display', 'qr_code_display')
    
    list_filter = ('disponivel', 'data_aquisicao', 'titulo__editora')
    
    search_fields = ('codigo_exemplar', 'titulo__titulo_da_obra', 'titulo__autor')
    
    ordering = ('titulo__titulo_da_obra', 'codigo_exemplar')
    
    readonly_fields = ('codigo_exemplar', 'qr_code_display', 'created_at', 'updated_at')
    
    def esta_emprestado_display(self, obj):
        """Exibe se o exemplar está emprestado"""
        if obj.esta_emprestado():
            emprestimo = obj.emprestimo_atual()
            return format_html(
                '<span style="color: orange;">Emprestado para {}</span>',
                emprestimo.aluno.nome
            )
        return format_html('<span style="color: green;">Disponível</span>')
    
    esta_emprestado_display.short_description = 'Status do Empréstimo'
    
    def qr_code_display(self, obj):
        """Exibe o QR Code como imagem"""
        if obj.qr_code:
            return format_html(
                '<img src="{}" width="100" height="100" />',
                obj.qr_code.url
            )
        return "Sem QR Code"
    
    qr_code_display.short_description = 'QR Code'


@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    """Admin para o modelo Emprestimo"""
    
    list_display = ('aluno', 'exemplar_titulo', 'data_emprestimo', 
                   'previsao_devolucao', 'data_devolucao', 'status_display', 
                   'dias_restantes_display')
    
    list_filter = ('data_emprestimo', 'previsao_devolucao', 'data_devolucao')
    
    search_fields = ('aluno__nome', 'aluno__serie',
                    'exemplar__titulo__titulo_da_obra', 'exemplar__codigo_exemplar')
    
    ordering = ('-data_emprestimo',)
    
    readonly_fields = ('data_emprestimo', 'created_at', 'updated_at')
    
    actions = ['devolver_livros']
    
    def exemplar_titulo(self, obj):
        """Exibe o título do exemplar"""
        return obj.exemplar.titulo.titulo_da_obra
    
    exemplar_titulo.short_description = 'Título'
    
    def status_display(self, obj):
        """Exibe o status do empréstimo com cores"""
        if obj.data_devolucao:
            return format_html('<span style="color: green; font-weight: bold;">Devolvido</span>')
        elif obj.esta_atrasado():
            return format_html(
                '<span style="color: red; font-weight: bold;">Atrasado ({} dias)</span>',
                obj.dias_atraso()
            )
        else:
            return format_html('<span style="color: blue;">Em andamento</span>')
    
    status_display.short_description = 'Status'
    
    def dias_restantes_display(self, obj):
        """Exibe dias restantes ou atraso"""
        if obj.data_devolucao:
            return "-"
        
        dias = obj.dias_para_vencimento()
        if dias < 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">{} dias de atraso</span>',
                abs(dias)
            )
        elif dias <= 7:
            return format_html(
                '<span style="color: orange; font-weight: bold;">{} dias restantes</span>',
                dias
            )
        else:
            return f"{dias} dias restantes"
    
    dias_restantes_display.short_description = 'Prazo'
    
    def devolver_livros(self, request, queryset):
        """Ação para devolver múltiplos livros"""
        count = 0
        for emprestimo in queryset:
            if not emprestimo.data_devolucao:
                emprestimo.devolver()
                count += 1
        
        self.message_user(request, f'{count} livros foram devolvidos com sucesso.')
    
    devolver_livros.short_description = "Devolver livros selecionados"


@admin.register(HistoricoEmprestimo)
class HistoricoEmprestimoAdmin(admin.ModelAdmin):
    """Admin para o modelo HistoricoEmprestimo"""
    
    list_display = ('emprestimo', 'renovacoes', 'notificacoes_enviadas', 'ultima_notificacao')
    
    list_filter = ('renovacoes', 'notificacoes_enviadas')
    
    search_fields = ('emprestimo__aluno__nome',)
    
    readonly_fields = ('emprestimo',)


# Customização do site admin
admin.site.site_header = "Sistema de Biblioteca - Administração"
admin.site.site_title = "Biblioteca Admin"
admin.site.index_title = "Painel de Administração da Biblioteca"
