from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from datetime import timedelta
import json

from .models import Usuario, Aluno, Titulo, Exemplar, Emprestimo, HistoricoEmprestimo
from .forms import (
    LoginForm, AlunoForm, TituloForm, ExemplarForm,
    EmprestimoForm, BuscaAcervoForm, DevolucaoForm
)


def is_administrador(user):
    """Verifica se o usuário é administrador"""
    return user.is_authenticated and user.is_administrador


# ==========================================================================
# Views públicas
# ==========================================================================

def home(request):
    """Página inicial"""
    context = {
        'total_titulos': Titulo.objects.count(),
        'total_exemplares': Exemplar.objects.count(),
        'exemplares_disponiveis': Exemplar.objects.filter(disponivel=True).count(),
        'emprestimos_ativos': Emprestimo.objects.filter(data_devolucao__isnull=True).count(),
    }
    return render(request, 'biblioteca/home.html', context)


def logout_view(request):
    """Logout do administrador"""
    if request.method in ('POST', 'GET'):
        if request.user.is_authenticated:
            nome = request.user.first_name or request.user.username
            logout(request)
            messages.success(request, f'Você foi desconectado com sucesso, {nome}!')
        return redirect('home')
    return redirect('home')


def acervo(request):
    """Consulta pública do acervo"""
    form = BuscaAcervoForm(request.GET)
    titulos = Titulo.objects.all()

    if form.is_valid():
        termo_busca = form.cleaned_data.get('termo_busca')
        tipo_busca = form.cleaned_data.get('tipo_busca')
        editora = form.cleaned_data.get('editora')
        ano_inicio = form.cleaned_data.get('ano_inicio')
        ano_fim = form.cleaned_data.get('ano_fim')

        if termo_busca:
            if tipo_busca == 'titulo':
                titulos = titulos.filter(titulo_da_obra__icontains=termo_busca)
            elif tipo_busca == 'autor':
                titulos = titulos.filter(autor__icontains=termo_busca)
            else:  # todos
                titulos = titulos.filter(
                    Q(titulo_da_obra__icontains=termo_busca) |
                    Q(autor__icontains=termo_busca)
                )

        if editora:
            titulos = titulos.filter(editora__icontains=editora)

        if ano_inicio:
            titulos = titulos.filter(ano_publicacao__gte=ano_inicio)

        if ano_fim:
            titulos = titulos.filter(ano_publicacao__lte=ano_fim)

    # Paginação
    paginator = Paginator(titulos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'form': form,
        'page_obj': page_obj,
        'total_resultados': titulos.count()
    }
    return render(request, 'biblioteca/acervo.html', context)


def exemplar_detail(request, exemplar_id):
    """Detalhes do exemplar via QR Code"""
    exemplar = get_object_or_404(Exemplar, id=exemplar_id)

    context = {
        'exemplar': exemplar,
        'emprestimo_atual': exemplar.emprestimo_atual() if exemplar.esta_emprestado() else None,
    }
    return render(request, 'biblioteca/exemplar_detail.html', context)


# ==========================================================================
# Views administrativas
# ==========================================================================

@user_passes_test(is_administrador)
def admin_dashboard(request):
    """Dashboard administrativo"""
    context = {
        'total_alunos': Aluno.objects.count(),
        'total_titulos': Titulo.objects.count(),
        'total_exemplares': Exemplar.objects.count(),
        'emprestimos_ativos': Emprestimo.objects.filter(data_devolucao__isnull=True).count(),
        'emprestimos_atrasados': Emprestimo.objects.filter(
            data_devolucao__isnull=True,
            previsao_devolucao__lt=timezone.now().date()
        ).count(),
        'alunos_suspensos': sum(1 for a in Aluno.objects.all() if a.esta_suspenso()),
    }
    return render(request, 'biblioteca/admin/dashboard.html', context)


@user_passes_test(is_administrador)
def titulo_list(request):
    """Lista de títulos para administradores"""
    titulos = Titulo.objects.all().order_by('titulo_da_obra')

    busca = request.GET.get('busca', '')
    if busca:
        titulos = titulos.filter(
            Q(titulo_da_obra__icontains=busca) |
            Q(autor__icontains=busca) |
            Q(lombada__icontains=busca)
        )

    paginator = Paginator(titulos, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'biblioteca/admin/titulo_list.html', {
        'page_obj': page_obj,
        'busca': busca
    })


@user_passes_test(is_administrador)
def titulo_create(request):
    """Criar novo título"""
    if request.method == 'POST':
        form = TituloForm(request.POST)
        if form.is_valid():
            titulo = form.save()
            messages.success(request, f'Título "{titulo.titulo_da_obra}" criado com sucesso!')
            return redirect('titulo_list')
    else:
        form = TituloForm()

    return render(request, 'biblioteca/admin/titulo_form.html', {
        'form': form,
        'action': 'Criar'
    })


@user_passes_test(is_administrador)
def titulo_edit(request, titulo_id):
    """Editar título"""
    titulo = get_object_or_404(Titulo, id=titulo_id)

    if request.method == 'POST':
        form = TituloForm(request.POST, instance=titulo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Título "{titulo.titulo_da_obra}" atualizado com sucesso!')
            return redirect('titulo_list')
    else:
        form = TituloForm(instance=titulo)

    return render(request, 'biblioteca/admin/titulo_form.html', {
        'form': form,
        'titulo': titulo,
        'action': 'Editar'
    })


@user_passes_test(is_administrador)
def titulo_delete(request, titulo_id):
    """Excluir título"""
    titulo = get_object_or_404(Titulo, id=titulo_id)

    if request.method == 'POST':
        nome_titulo = titulo.titulo_da_obra
        titulo.delete()
        messages.success(request, f'Título "{nome_titulo}" excluído com sucesso!')
        return redirect('titulo_list')

    return render(request, 'biblioteca/admin/titulo_confirm_delete.html', {
        'titulo': titulo,
        'object': titulo,
    })


@user_passes_test(is_administrador)
def exemplar_list(request):
    """Lista de exemplares"""
    exemplares = Exemplar.objects.select_related('titulo').all()

    titulo_id = request.GET.get('titulo')
    disponivel = request.GET.get('disponivel')
    busca = request.GET.get('busca', '')

    if titulo_id:
        exemplares = exemplares.filter(titulo_id=titulo_id)

    if disponivel == 'sim':
        exemplares = exemplares.filter(disponivel=True)
    elif disponivel == 'nao':
        exemplares = exemplares.filter(disponivel=False)

    if busca:
        exemplares = exemplares.filter(
            Q(titulo__titulo_da_obra__icontains=busca) |
            Q(titulo__autor__icontains=busca) |
            Q(codigo_exemplar__icontains=busca) |
            Q(titulo__lombada__icontains=busca)
        )

    paginator = Paginator(exemplares, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_exemplares = Exemplar.objects.count()
    disponiveis = Exemplar.objects.filter(disponivel=True).count()
    emprestados = total_exemplares - disponiveis
    titulos_diferentes = Titulo.objects.count()

    titulos = Titulo.objects.all().order_by("titulo_da_obra")

    context = {
        'page_obj': page_obj,
        'titulos': titulos,
        'titulo_selecionado': titulo_id,
        'disponivel_selecionado': disponivel,
        'busca': busca,
        'titulo_filtro': titulo_id,
        'disponivel': disponivel,
        'total_exemplares': total_exemplares,
        'disponiveis': disponiveis,
        'emprestados': emprestados,
        'titulos_diferentes': titulos_diferentes,
    }
    return render(request, 'biblioteca/admin/exemplar_list.html', context)


@user_passes_test(is_administrador)
def exemplar_create(request):
    """Criar novo exemplar"""
    if request.method == 'POST':
        form = ExemplarForm(request.POST)
        if form.is_valid():
            exemplar = form.save()
            messages.success(request, f'Exemplar "{exemplar.codigo_exemplar}" criado com sucesso!')
            return redirect('exemplar_list')
    else:
        form = ExemplarForm()

    return render(request, 'biblioteca/admin/exemplar_form.html', {
        'form': form,
        'action': 'Criar'
    })


@user_passes_test(is_administrador)
def exemplar_delete(request, exemplar_id):
    """Excluir exemplar"""
    exemplar = get_object_or_404(Exemplar, id=exemplar_id)

    if request.method == 'POST':
        codigo = exemplar.codigo_exemplar
        exemplar.delete()
        messages.success(request, f'Exemplar "{codigo}" excluído com sucesso!')
        return redirect('exemplar_list')

    return render(request, 'biblioteca/admin/exemplar_confirm_delete.html', {
        'exemplar': exemplar,
        'object': exemplar,
    })


@user_passes_test(is_administrador)
def emprestimo_list(request):
    """Lista de empréstimos"""
    emprestimos = Emprestimo.objects.select_related('aluno', 'exemplar__titulo').all()

    status = request.GET.get('status')
    busca = request.GET.get('busca', '')
    periodo = request.GET.get('periodo', '')
    ordem = request.GET.get('ordem', 'recente')

    if status == 'ativo':
        emprestimos = emprestimos.filter(data_devolucao__isnull=True)
    elif status == 'devolvido':
        emprestimos = emprestimos.filter(data_devolucao__isnull=False)
    elif status == 'atrasado':
        emprestimos = emprestimos.filter(
            data_devolucao__isnull=True,
            previsao_devolucao__lt=timezone.now().date()
        )

    if busca:
        emprestimos = emprestimos.filter(
            Q(aluno__nome__icontains=busca) |
            Q(aluno__serie__icontains=busca) |
            Q(exemplar__titulo__titulo_da_obra__icontains=busca) |
            Q(exemplar__codigo_exemplar__icontains=busca)
        )

    hoje = timezone.now().date()
    if periodo == 'hoje':
        emprestimos = emprestimos.filter(data_emprestimo__date=hoje)
    elif periodo == 'semana':
        start_of_week = hoje - timedelta(days=hoje.weekday())
        emprestimos = emprestimos.filter(data_emprestimo__date__gte=start_of_week)
    elif periodo == 'mes':
        emprestimos = emprestimos.filter(
            data_emprestimo__year=hoje.year,
            data_emprestimo__month=hoje.month
        )

    if ordem == 'recente':
        emprestimos = emprestimos.order_by('-data_emprestimo')
    elif ordem == 'antigo':
        emprestimos = emprestimos.order_by('data_emprestimo')
    elif ordem == 'vencimento':
        emprestimos = emprestimos.order_by('previsao_devolucao')
    elif ordem == 'aluno':
        emprestimos = emprestimos.order_by('aluno__nome')

    paginator = Paginator(emprestimos, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_emprestimos = Emprestimo.objects.count()
    emprestimos_ativos = Emprestimo.objects.filter(data_devolucao__isnull=True).count()
    emprestimos_atrasados = Emprestimo.objects.filter(
        data_devolucao__isnull=True,
        previsao_devolucao__lt=timezone.now().date()
    ).count()
    emprestimos_devolvidos = Emprestimo.objects.filter(data_devolucao__isnull=False).count()

    return render(request, 'biblioteca/admin/emprestimo_list.html', {
        'page_obj': page_obj,
        'status_selecionado': status,
        'busca': busca,
        'status': status,
        'periodo': periodo,
        'ordem': ordem,
        'total_emprestimos': total_emprestimos,
        'emprestimos_ativos': emprestimos_ativos,
        'emprestimos_atrasados': emprestimos_atrasados,
        'emprestimos_devolvidos': emprestimos_devolvidos,
    })


@user_passes_test(is_administrador)
def emprestimo_create(request):
    """Criar novo empréstimo (admin escolhe o aluno numa lista/busca)"""
    if request.method == 'POST':
        form = EmprestimoForm(request.POST)
        if form.is_valid():
            emprestimo = form.save()
            messages.success(request, f'Empréstimo realizado para {emprestimo.aluno.nome}!')
            return redirect('emprestimo_list')
    else:
        form = EmprestimoForm()

    return render(request, 'biblioteca/admin/emprestimo_form.html', {
        'form': form,
        'action': 'Criar'
    })


@user_passes_test(is_administrador)
def emprestimo_detail(request, emprestimo_id):
    """Página de detalhes do empréstimo"""
    emprestimo = get_object_or_404(Emprestimo, id=emprestimo_id)

    dias_emprestado = (timezone.now().date() - emprestimo.data_emprestimo.date()).days

    if emprestimo.data_devolucao:
        dias_total = (emprestimo.data_devolucao - emprestimo.data_emprestimo).days
        status_devolucao = "devolvido"
        if emprestimo.data_devolucao.date() > emprestimo.previsao_devolucao:
            dias_atraso = (emprestimo.data_devolucao.date() - emprestimo.previsao_devolucao).days
        else:
            dias_atraso = 0
    else:
        dias_total = dias_emprestado
        if emprestimo.previsao_devolucao < timezone.now().date():
            status_devolucao = "atrasado"
            dias_atraso = (timezone.now().date() - emprestimo.previsao_devolucao).days
        else:
            status_devolucao = "ativo"
            dias_atraso = 0

    outros_emprestimos = Emprestimo.objects.filter(
        aluno=emprestimo.aluno
    ).exclude(id=emprestimo_id).select_related('exemplar__titulo').order_by('-data_emprestimo')[:5]

    outros_emprestimos_livro = Emprestimo.objects.filter(
        exemplar__titulo=emprestimo.exemplar.titulo
    ).exclude(id=emprestimo_id).select_related('aluno').order_by('-data_emprestimo')[:5]

    context = {
        'emprestimo': emprestimo,
        'dias_emprestado': dias_emprestado,
        'dias_total': dias_total,
        'dias_atraso': dias_atraso,
        'status_devolucao': status_devolucao,
        'outros_emprestimos': outros_emprestimos,
        'outros_emprestimos_livro': outros_emprestimos_livro,
    }

    return render(request, 'biblioteca/admin/emprestimo_detail.html', context)


@user_passes_test(is_administrador)
def devolver_exemplar(request, exemplar_id):
    """Realizar devolução de um exemplar específico (via admin, ex: pelo QR Code)"""
    exemplar = get_object_or_404(Exemplar, id=exemplar_id)

    try:
        emprestimo = Emprestimo.objects.get(
            exemplar=exemplar,
            data_devolucao__isnull=True
        )
    except Emprestimo.DoesNotExist:
        messages.error(request, 'Este exemplar não está emprestado.')
        return redirect('exemplar_detail', exemplar_id=exemplar_id)

    emprestimo.devolver()

    dias_atraso = emprestimo.dias_atraso()

    if dias_atraso > 0:
        messages.warning(
            request,
            f'Devolução realizada com {dias_atraso} dia(s) de atraso. '
            f'O aluno ficará suspenso por {dias_atraso} dia(s) a partir de hoje.'
        )
    else:
        messages.success(request, 'Devolução realizada com sucesso!')

    next_url = request.GET.get('next')
    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect('admin_dashboard')


@user_passes_test(is_administrador)
def devolucao(request):
    """Realizar devolução"""
    emprestimo_encontrado = None

    if request.method == 'POST':
        form = DevolucaoForm(request.POST)
        if form.is_valid():
            codigo_exemplar = form.cleaned_data['codigo_exemplar']

            try:
                exemplar = Exemplar.objects.get(codigo_exemplar=codigo_exemplar)
                emprestimo = Emprestimo.objects.filter(
                    exemplar=exemplar,
                    data_devolucao__isnull=True
                ).first()

                if emprestimo:
                    emprestimo_encontrado = emprestimo
                else:
                    messages.error(request, 'Este exemplar não está emprestado.')

            except Exemplar.DoesNotExist:
                messages.error(request, 'Exemplar não encontrado.')
    else:
        form = DevolucaoForm()

    emprestimos_ativos = Emprestimo.objects.filter(
        data_devolucao__isnull=True
    ).select_related('aluno', 'exemplar__titulo').order_by('-data_emprestimo')[:10]

    context = {
        'form': form,
        'emprestimo_encontrado': emprestimo_encontrado,
        'emprestimos_ativos': emprestimos_ativos,
        'emprestimos_hoje': Emprestimo.objects.filter(
            data_emprestimo__date=timezone.now().date()
        ).count(),
        'devolucoes_hoje': Emprestimo.objects.filter(
            data_devolucao__date=timezone.now().date()
        ).count(),
        'total_ativos': Emprestimo.objects.filter(data_devolucao__isnull=True).count(),
        'total_atrasados': Emprestimo.objects.filter(
            data_devolucao__isnull=True,
            previsao_devolucao__lt=timezone.now().date()
        ).count(),
    }

    return render(request, 'biblioteca/admin/devolucao.html', context)


# ==========================================================================
# Gestão de alunos (cadastro simples: nome, idade, gênero, série)
# ==========================================================================

@user_passes_test(is_administrador)
def aluno_list(request):
    """Lista de alunos cadastrados"""
    alunos = Aluno.objects.annotate(
        total_emprestimos=Count('emprestimos'),
        emprestimos_ativos_count=Count('emprestimos', filter=Q(emprestimos__data_devolucao__isnull=True))
    ).order_by('nome')

    status = request.GET.get('status')
    busca = request.GET.get('busca')
    genero = request.GET.get('genero')
    serie = request.GET.get('serie')
    ordem = request.GET.get('ordem', 'nome')

    if status == 'suspenso':
        ids_suspensos = [a.id for a in alunos if a.esta_suspenso()]
        alunos = alunos.filter(id__in=ids_suspensos)
    elif status == 'ativo':
        ids_ativos = [a.id for a in alunos if not a.esta_suspenso()]
        alunos = alunos.filter(id__in=ids_ativos)

    if busca:
        alunos = alunos.filter(
            Q(nome__icontains=busca) |
            Q(serie__icontains=busca)
        )

    if genero:
        alunos = alunos.filter(genero=genero)

    if serie:
        alunos = alunos.filter(serie=serie)

    if ordem == 'data':
        alunos = alunos.order_by('-created_at')
    elif ordem == 'emprestimos':
        alunos = alunos.order_by('-total_emprestimos')
    elif ordem == 'idade':
        alunos = alunos.order_by('idade')
    elif ordem == 'genero':
        alunos = alunos.order_by('genero')
    elif ordem == 'serie':
        alunos = alunos.order_by('serie')
    else:  # nome
        alunos = alunos.order_by('nome')

    paginator = Paginator(alunos, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    todos_os_alunos = Aluno.objects.all()
    total_alunos = todos_os_alunos.count()
    total_suspensos = sum(1 for a in todos_os_alunos if a.esta_suspenso())
    total_ativos = total_alunos - total_suspensos

    return render(request, 'biblioteca/admin/aluno_list.html', {
        'page_obj': page_obj,
        'status': status,
        'busca': busca,
        'genero': genero,
        'serie': serie,
        'ordem': ordem,
        'genero_choices': Aluno.GENERO_CHOICES,
        'serie_choices': Aluno.SERIE_CHOICES,
        'total_alunos': total_alunos,
        'total_ativos': total_ativos,
        'total_suspensos': total_suspensos,
    })


@user_passes_test(is_administrador)
def aluno_create(request):
    """Cadastrar novo aluno (nome, idade, gênero e série)"""
    if request.method == 'POST':
        form = AlunoForm(request.POST)
        if form.is_valid():
            aluno = form.save()
            messages.success(request, f'Aluno "{aluno.nome}" cadastrado com sucesso!')
            return redirect('aluno_list')
    else:
        form = AlunoForm()

    return render(request, 'biblioteca/admin/aluno_form.html', {
        'form': form,
        'action': 'Cadastrar'
    })


@user_passes_test(is_administrador)
def aluno_edit(request, aluno_id):
    """Editar cadastro de aluno"""
    aluno = get_object_or_404(Aluno, id=aluno_id)

    if request.method == 'POST':
        form = AlunoForm(request.POST, instance=aluno)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cadastro de "{aluno.nome}" atualizado com sucesso!')
            return redirect('aluno_list')
    else:
        form = AlunoForm(instance=aluno)

    return render(request, 'biblioteca/admin/aluno_form.html', {
        'form': form,
        'aluno': aluno,
        'action': 'Editar'
    })


@user_passes_test(is_administrador)
def aluno_delete(request, aluno_id):
    """Excluir cadastro de aluno"""
    aluno = get_object_or_404(Aluno, id=aluno_id)

    if request.method == 'POST':
        nome = aluno.nome
        aluno.delete()
        messages.success(request, f'Aluno "{nome}" excluído com sucesso!')
        return redirect('aluno_list')

    return render(request, 'biblioteca/admin/aluno_confirm_delete.html', {
        'aluno': aluno,
        'object': aluno,
    })


@user_passes_test(is_administrador)
def aluno_detail(request, aluno_id):
    """Página de detalhes do aluno"""
    aluno = get_object_or_404(Aluno, id=aluno_id)

    emprestimos_recentes = Emprestimo.objects.filter(
        aluno=aluno
    ).select_related('exemplar__titulo').order_by('-data_emprestimo')[:10]

    total_emprestimos = Emprestimo.objects.filter(aluno=aluno).count()
    emprestimos_ativos = Emprestimo.objects.filter(
        aluno=aluno,
        data_devolucao__isnull=True
    ).count()
    emprestimos_atrasados = Emprestimo.objects.filter(
        aluno=aluno,
        data_devolucao__isnull=True,
        previsao_devolucao__lt=timezone.now().date()
    ).count()

    context = {
        'aluno': aluno,
        'emprestimos_recentes': emprestimos_recentes,
        'total_emprestimos': total_emprestimos,
        'emprestimos_ativos': emprestimos_ativos,
        'emprestimos_atrasados': emprestimos_atrasados,
    }

    return render(request, 'biblioteca/admin/aluno_detail.html', context)


@user_passes_test(is_administrador)
def suspender_aluno(request, aluno_id):
    """Suspender aluno"""
    if request.method == 'POST':
        try:
            aluno = get_object_or_404(Aluno, id=aluno_id)
            aluno.suspender(30)

            return JsonResponse({
                'success': True,
                'message': f'Aluno {aluno.nome} suspenso por 30 dias'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({'success': False, 'error': 'Método não permitido'})


@user_passes_test(is_administrador)
def reativar_aluno(request, aluno_id):
    """Reativar aluno suspenso"""
    if request.method == 'POST':
        try:
            aluno = get_object_or_404(Aluno, id=aluno_id)
            aluno.reativar()

            return JsonResponse({
                'success': True,
                'message': f'Aluno {aluno.nome} reativado com sucesso'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({'success': False, 'error': 'Método não permitido'})


@user_passes_test(is_administrador)
def relatorios(request):
    """Página de relatórios administrativos"""
    from django.db.models.functions import TruncMonth

    todos_os_alunos = Aluno.objects.all()
    total_alunos = todos_os_alunos.count()
    total_suspensos = sum(1 for a in todos_os_alunos if a.esta_suspenso())
    total_ativos = total_alunos - total_suspensos
    total_titulos = Titulo.objects.count()
    total_exemplares = Exemplar.objects.count()
    total_emprestimos = Emprestimo.objects.count()

    emprestimos_ativos = Emprestimo.objects.filter(data_devolucao__isnull=True).count()
    emprestimos_atrasados_count = Emprestimo.objects.filter(
        data_devolucao__isnull=True,
        previsao_devolucao__lt=timezone.now().date()
    ).count()
    emprestimos_devolvidos = Emprestimo.objects.filter(data_devolucao__isnull=False).count()

    if total_emprestimos > 0:
        percentual_ativos = (emprestimos_ativos / total_emprestimos) * 100
        percentual_atrasados = (emprestimos_atrasados_count / total_emprestimos) * 100
        percentual_devolvidos = (emprestimos_devolvidos / total_emprestimos) * 100
    else:
        percentual_ativos = percentual_atrasados = percentual_devolvidos = 0

    livros_mais_emprestados = Emprestimo.objects.values('exemplar__titulo__titulo_da_obra', 'exemplar__titulo__autor')\
        .annotate(total=Count('exemplar__titulo'))\
        .order_by('-total')[:10]

    alunos_mais_ativos = Emprestimo.objects.values('aluno__nome', 'aluno__serie')\
        .annotate(total=Count('aluno'))\
        .order_by('-total')[:10]

    emprestimos_por_mes = Emprestimo.objects.filter(
        data_emprestimo__gte=timezone.now() - timedelta(days=365)
    ).annotate(mes=TruncMonth('data_emprestimo'))\
        .values('mes').annotate(total=Count('id')).order_by('mes')

    emprestimos_atrasados_lista = Emprestimo.objects.filter(
        data_devolucao__isnull=True,
        previsao_devolucao__lt=timezone.now().date()
    ).order_by('previsao_devolucao')

    context = {
        'total_usuarios': total_alunos,
        'total_alunos': total_alunos,
        'total_titulos': total_titulos,
        'total_exemplares': total_exemplares,
        'total_emprestimos': total_emprestimos,

        'emprestimos_ativos': emprestimos_ativos,
        'emprestimos_atrasados': emprestimos_atrasados_count,
        'emprestimos_devolvidos': emprestimos_devolvidos,
        'percentual_ativos': percentual_ativos,
        'percentual_atrasados': percentual_atrasados,
        'percentual_devolvidos': percentual_devolvidos,

        'livros_mais_emprestados': livros_mais_emprestados,
        'usuarios_mais_ativos': alunos_mais_ativos,
        'alunos_mais_ativos': alunos_mais_ativos,

        'emprestimos_por_mes': list(emprestimos_por_mes),

        'emprestimos_atrasados_lista': emprestimos_atrasados_lista,
    }

    return render(request, 'biblioteca/admin/relatorios.html', context)


# ==========================================================================
# API Views para AJAX
# ==========================================================================

@login_required
@require_http_methods(["GET"])
def api_exemplares_titulo(request, titulo_id):
    """API para buscar exemplares de um título específico"""
    exemplares = Exemplar.objects.filter(
        titulo_id=titulo_id,
        disponivel=True
    ).values('id', 'codigo_exemplar')

    return JsonResponse(list(exemplares), safe=False)


@login_required
@require_http_methods(["POST"])
def api_verificar_disponibilidade(request):
    """API para verificar disponibilidade de exemplar"""
    data = json.loads(request.body)
    codigo_exemplar = data.get('codigo_exemplar')

    try:
        exemplar = Exemplar.objects.get(codigo_exemplar=codigo_exemplar)
        return JsonResponse({
            'disponivel': exemplar.disponivel,
            'titulo': exemplar.titulo.titulo_da_obra,
            'autor': exemplar.titulo.autor
        })
    except Exemplar.DoesNotExist:
        return JsonResponse({'error': 'Exemplar não encontrado'}, status=404)


@require_http_methods(["GET"])
def api_aluno_status(request, aluno_id):
    """Retorna status e dados do aluno para AJAX do formulário de empréstimo"""
    aluno = get_object_or_404(Aluno, id=aluno_id)
    emprestimos_ativos = Emprestimo.objects.filter(aluno=aluno, data_devolucao__isnull=True).count()
    status = "Ativo"
    if aluno.esta_suspenso():
        if aluno.data_suspensao and aluno.data_suspensao >= timezone.now().date():
            status = f"Suspenso até {aluno.data_suspensao.strftime('%d/%m/%Y')}"
        elif aluno.tem_emprestimo_atrasado():
            status = "Suspenso por atraso"
        else:
            status = "Suspenso"
    pode_emprestar = aluno.pode_emprestar()
    return JsonResponse({
        "status": status,
        "emprestimos_ativos": emprestimos_ativos,
        "pode_emprestar": pode_emprestar,
        "nome": aluno.nome,
        "serie": aluno.serie,
    })
