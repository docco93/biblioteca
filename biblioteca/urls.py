from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import LoginForm

urlpatterns = [
    # URLs públicas
    path('', views.home, name='home'),
    path('acervo/', views.acervo, name='acervo'),
    path('exemplar/<int:exemplar_id>/', views.exemplar_detail, name='exemplar_detail'),

    # Autenticação (apenas administrador)
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=LoginForm,
    ), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # URLs administrativas
    path('painel/', views.admin_dashboard, name='admin_dashboard'),

    # Gestão de alunos (cadastro: nome, idade, gênero, série)
    path('painel/alunos/', views.aluno_list, name='aluno_list'),
    path('painel/alunos/criar/', views.aluno_create, name='aluno_create'),
    path('painel/alunos/<int:aluno_id>/', views.aluno_detail, name='aluno_detail'),
    path('painel/alunos/<int:aluno_id>/editar/', views.aluno_edit, name='aluno_edit'),
    path('painel/alunos/<int:aluno_id>/excluir/', views.aluno_delete, name='aluno_delete'),
    path('painel/alunos/<int:aluno_id>/suspender/', views.suspender_aluno, name='suspender_aluno'),
    path('painel/alunos/<int:aluno_id>/reativar/', views.reativar_aluno, name='reativar_aluno'),

    # Gestão de títulos
    path('painel/titulos/', views.titulo_list, name='titulo_list'),
    path('painel/titulos/criar/', views.titulo_create, name='titulo_create'),
    path('painel/titulos/<int:titulo_id>/editar/', views.titulo_edit, name='titulo_edit'),
    path('painel/titulos/<int:titulo_id>/excluir/', views.titulo_delete, name='titulo_delete'),

    # Gestão de exemplares
    path('painel/exemplares/', views.exemplar_list, name='exemplar_list'),
    path('painel/exemplares/criar/', views.exemplar_create, name='exemplar_create'),
    path('painel/exemplares/<int:exemplar_id>/excluir/', views.exemplar_delete, name='exemplar_delete'),
    # Compatibilidade: rota curta para exclusão de exemplar (mantém checagem de administrador na view)
    path('exemplar/<int:exemplar_id>/excluir/', views.exemplar_delete, name='exemplar_delete_public'),
    path('exemplar/<int:exemplar_id>/devolver/', views.devolver_exemplar, name='devolver_exemplar'),

    # Gestão de empréstimos
    path('painel/emprestimos/', views.emprestimo_list, name='emprestimo_list'),
    path('painel/emprestimos/<int:emprestimo_id>/', views.emprestimo_detail, name='emprestimo_detail'),
    path('painel/emprestimos/criar/', views.emprestimo_create, name='emprestimo_create'),
    path('painel/devolucao/', views.devolucao, name='devolucao'),

    # Relatórios
    path('painel/relatorios/', views.relatorios, name='relatorios'),

    # APIs
    path('api/exemplares/<int:titulo_id>/', views.api_exemplares_titulo, name='api_exemplares_titulo'),
    path('api/verificar-disponibilidade/', views.api_verificar_disponibilidade, name='api_verificar_disponibilidade'),
    path('api/aluno/<int:aluno_id>/', views.api_aluno_status, name='api_aluno_status'),
]
