from django.utils import timezone
from datetime import timedelta
from .models import Emprestimo, Aluno, Titulo, Exemplar, HistoricoEmprestimo


class EmprestimoService:
    """Serviço para gerenciar regras de negócio de empréstimos"""

    PRAZO_PADRAO_DIAS = 30
    LIMITE_LIVROS_POR_ALUNO = 3
    DIAS_NOTIFICACAO_ANTECIPADA = 7

    @classmethod
    def pode_emprestar(cls, aluno, exemplar):
        """
        Verifica se um aluno pode emprestar um exemplar específico
        Retorna (pode_emprestar: bool, motivo: str)
        """
        if aluno.esta_suspenso():
            return False, f"Aluno suspenso até {aluno.data_suspensao.strftime('%d/%m/%Y')}" if aluno.data_suspensao else "Aluno suspenso"

        emprestimos_ativos = Emprestimo.objects.filter(
            aluno=aluno,
            data_devolucao__isnull=True
        ).count()

        if emprestimos_ativos >= cls.LIMITE_LIVROS_POR_ALUNO:
            return False, f"Limite de {cls.LIMITE_LIVROS_POR_ALUNO} livros atingido"

        if not exemplar.disponivel:
            return False, "Exemplar não disponível"

        titulo_ja_emprestado = Emprestimo.objects.filter(
            aluno=aluno,
            exemplar__titulo=exemplar.titulo,
            data_devolucao__isnull=True
        ).exists()

        if titulo_ja_emprestado:
            return False, "Aluno já possui um exemplar deste título"

        return True, "Pode emprestar"

    @classmethod
    def realizar_emprestimo(cls, aluno, exemplar, observacoes=""):
        """
        Realiza um empréstimo seguindo todas as regras de negócio
        Retorna (emprestimo: Emprestimo, sucesso: bool, mensagem: str)
        """
        pode_emprestar, motivo = cls.pode_emprestar(aluno, exemplar)

        if not pode_emprestar:
            return None, False, motivo

        emprestimo = Emprestimo.objects.create(
            aluno=aluno,
            exemplar=exemplar,
            previsao_devolucao=timezone.now().date() + timedelta(days=cls.PRAZO_PADRAO_DIAS),
            observacoes=observacoes
        )

        HistoricoEmprestimo.objects.create(emprestimo=emprestimo)

        return emprestimo, True, "Empréstimo realizado com sucesso"

    @classmethod
    def realizar_devolucao(cls, exemplar, observacoes=""):
        """
        Realiza a devolução de um exemplar
        Retorna (emprestimo: Emprestimo, sucesso: bool, mensagem: str)
        """
        try:
            emprestimo = Emprestimo.objects.get(
                exemplar=exemplar,
                data_devolucao__isnull=True
            )
        except Emprestimo.DoesNotExist:
            return None, False, "Exemplar não está emprestado"

        dias_atraso = 0
        if emprestimo.esta_atrasado():
            dias_atraso = emprestimo.dias_atraso()

        emprestimo.data_devolucao = timezone.now()
        if observacoes:
            emprestimo.observacoes += f"\nDevolução: {observacoes}"

        if dias_atraso > 0:
            cls.aplicar_suspensao(emprestimo.aluno, dias_atraso)

        exemplar.disponivel = True
        exemplar.save()
        emprestimo.save()

        mensagem = "Devolução realizada com sucesso"
        if dias_atraso > 0:
            mensagem += f". Aluno suspenso por {dias_atraso} dias devido ao atraso"

        return emprestimo, True, mensagem

    @classmethod
    def aplicar_suspensao(cls, aluno, dias_atraso):
        """Aplica suspensão ao aluno baseada nos dias de atraso"""
        data_suspensao = timezone.now().date() + timedelta(days=dias_atraso)

        if aluno.data_suspensao:
            if data_suspensao > aluno.data_suspensao:
                aluno.data_suspensao = data_suspensao
        else:
            aluno.data_suspensao = data_suspensao

        aluno.save()

    @classmethod
    def renovar_emprestimo(cls, emprestimo, dias_renovacao=30):
        """
        Renova um empréstimo por mais dias
        Retorna (sucesso: bool, mensagem: str)
        """
        if emprestimo.data_devolucao:
            return False, "Empréstimo já foi devolvido"

        if emprestimo.esta_atrasado():
            return False, "Não é possível renovar empréstimo em atraso"

        historico, created = HistoricoEmprestimo.objects.get_or_create(
            emprestimo=emprestimo
        )

        if historico.renovacoes >= 2:
            return False, "Limite de renovações atingido (máximo 2)"

        emprestimo.previsao_devolucao += timedelta(days=dias_renovacao)
        emprestimo.save()

        historico.renovacoes += 1
        historico.save()

        return True, f"Empréstimo renovado por {dias_renovacao} dias"


class RelatorioService:
    """Serviço para gerar relatórios administrativos"""

    @classmethod
    def livros_mais_emprestados(cls, limite=10):
        """Retorna os livros mais emprestados"""
        from django.db.models import Count

        return Titulo.objects.annotate(
            total_emprestimos=Count('exemplares__emprestimos')
        ).order_by('-total_emprestimos')[:limite]

    @classmethod
    def alunos_mais_ativos(cls, limite=10):
        """Retorna os alunos com mais empréstimos"""
        from django.db.models import Count

        return Aluno.objects.annotate(
            total_emprestimos=Count('emprestimos')
        ).order_by('-total_emprestimos')[:limite]

    @classmethod
    def emprestimos_atrasados(cls):
        """Retorna empréstimos em atraso"""
        return Emprestimo.objects.filter(
            data_devolucao__isnull=True,
            previsao_devolucao__lt=timezone.now().date()
        ).order_by('previsao_devolucao')

    @classmethod
    def estatisticas_gerais(cls):
        """Retorna estatísticas gerais do sistema"""
        total_alunos = Aluno.objects.count()
        alunos_suspensos = sum(1 for a in Aluno.objects.all() if a.esta_suspenso())
        alunos_ativos = total_alunos - alunos_suspensos

        total_titulos = Titulo.objects.count()
        total_exemplares = Exemplar.objects.count()
        exemplares_disponiveis = Exemplar.objects.filter(disponivel=True).count()

        total_emprestimos = Emprestimo.objects.count()
        emprestimos_ativos = Emprestimo.objects.filter(data_devolucao__isnull=True).count()
        emprestimos_atrasados = Emprestimo.objects.filter(
            data_devolucao__isnull=True,
            previsao_devolucao__lt=timezone.now().date()
        ).count()

        return {
            'alunos': {
                'total': total_alunos,
                'ativos': alunos_ativos,
                'suspensos': alunos_suspensos,
                'taxa_atividade': (alunos_ativos / total_alunos * 100) if total_alunos > 0 else 0
            },
            'acervo': {
                'total_titulos': total_titulos,
                'total_exemplares': total_exemplares,
                'exemplares_disponiveis': exemplares_disponiveis,
                'taxa_disponibilidade': (exemplares_disponiveis / total_exemplares * 100) if total_exemplares > 0 else 0
            },
            'emprestimos': {
                'total': total_emprestimos,
                'ativos': emprestimos_ativos,
                'atrasados': emprestimos_atrasados,
                'taxa_atraso': (emprestimos_atrasados / emprestimos_ativos * 100) if emprestimos_ativos > 0 else 0
            }
        }
