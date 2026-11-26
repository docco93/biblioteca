from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Lista empréstimos que estão vencendo ou atrasados (alunos não têm e-mail cadastrado, então este comando apenas exibe o relatório no console)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem marcar notificação (apenas mostra o relatório)',
        )

    def handle(self, *args, **options):
        from biblioteca.models import Emprestimo, HistoricoEmprestimo
        from biblioteca.utils import EmprestimoService
        from datetime import timedelta

        self.stdout.write(
            self.style.SUCCESS(
                f'Verificando empréstimos - {timezone.now().strftime("%d/%m/%Y %H:%M:%S")}'
            )
        )

        data_limite = timezone.now().date() + timedelta(days=EmprestimoService.DIAS_NOTIFICACAO_ANTECIPADA)

        emprestimos_vencendo = Emprestimo.objects.filter(
            data_devolucao__isnull=True,
            previsao_devolucao__lte=data_limite,
            previsao_devolucao__gte=timezone.now().date()
        ).select_related('aluno', 'exemplar__titulo')

        total_emprestimos = emprestimos_vencendo.count()
        self.stdout.write(f'Encontrados {total_emprestimos} empréstimos vencendo em breve:')

        for emprestimo in emprestimos_vencendo:
            historico, created = HistoricoEmprestimo.objects.get_or_create(emprestimo=emprestimo)
            dias_restantes = emprestimo.dias_para_vencimento()

            if not options['dry_run']:
                historico.notificacoes_enviadas += 1
                historico.ultima_notificacao = timezone.now()
                historico.save()

            self.stdout.write(
                f'  - {emprestimo.aluno.nome} ({emprestimo.exemplar.titulo.titulo_da_obra}) - {dias_restantes} dias restantes'
            )

        emprestimos_atrasados = Emprestimo.objects.filter(
            data_devolucao__isnull=True,
            previsao_devolucao__lt=timezone.now().date()
        ).select_related('aluno', 'exemplar__titulo')

        total_atrasados = emprestimos_atrasados.count()

        if total_atrasados > 0:
            self.stdout.write(self.style.ERROR(f'\nEmpréstimos em atraso: {total_atrasados}'))
            for emprestimo in emprestimos_atrasados:
                dias_atraso = emprestimo.dias_atraso()
                self.stdout.write(
                    self.style.ERROR(
                        f'  - {emprestimo.aluno.nome} ({emprestimo.exemplar.titulo.titulo_da_obra}) - {dias_atraso} dias de atraso'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nResumo:'
                f'\n- Empréstimos vencendo em breve: {total_emprestimos}'
                f'\n- Empréstimos em atraso: {total_atrasados}'
                f'\n- Finalizado em: {timezone.now().strftime("%d/%m/%Y %H:%M:%S")}'
            )
        )
