#!/usr/bin/env python3
import os
import re
import pandas as pd
from django.core.management.base import BaseCommand
from biblioteca.models import Aluno


class Command(BaseCommand):
    help = (
        'Importa alunos de uma planilha Excel para o banco de dados. '
        'A planilha deve ter as colunas: Nome, Idade, Gênero, Série.'
    )

    REGEX_NOME = re.compile(r'^[A-Za-zÀ-ÖØ-öø-ÿ\s]+$')

    # Aceita tanto a letra (M/F/O) quanto a palavra por extenso na planilha
    GENERO_MAP = {
        'M': 'M', 'MASCULINO': 'M',
        'F': 'F', 'FEMININO': 'F',
        'O': 'O', 'OUTRO': 'O',
    }

    def add_arguments(self, parser):
        parser.add_argument('caminho_planilha', type=str, help='O caminho para a planilha Excel a ser importada.')
        parser.add_argument(
            '--sheet',
            type=str,
            default=0,
            help='Nome ou índice da aba a ser lida (padrão: primeira aba).'
        )

    def handle(self, *args, **kwargs):
        caminho_planilha = kwargs['caminho_planilha']
        sheet = kwargs['sheet']

        if not os.path.exists(caminho_planilha):
            self.stdout.write(self.style.ERROR(f'Arquivo não encontrado em: {caminho_planilha}'))
            return

        try:
            df = pd.read_excel(caminho_planilha, sheet_name=sheet)
            self.stdout.write(self.style.SUCCESS(f'Planilha "{os.path.basename(caminho_planilha)}" lida com sucesso.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao ler a planilha: {e}'))
            return

        # Normaliza nomes das colunas (remove espaços extras, ignora maiúsculas/minúsculas e acentos comuns)
        df.columns = [str(c).strip() for c in df.columns]
        mapa_colunas = {}
        for coluna in df.columns:
            chave = coluna.strip().lower()
            if chave in ('nome',):
                mapa_colunas[coluna] = 'Nome'
            elif chave in ('idade',):
                mapa_colunas[coluna] = 'Idade'
            elif chave in ('gênero', 'genero'):
                mapa_colunas[coluna] = 'Gênero'
            elif chave in ('série', 'serie'):
                mapa_colunas[coluna] = 'Série'
        df = df.rename(columns=mapa_colunas)
        # Segurança: evita quebra caso a planilha tenha colunas duplicadas após a normalização
        df = df.loc[:, ~df.columns.duplicated()]

        colunas_necessarias = {'Nome', 'Idade', 'Gênero', 'Série'}
        faltando = colunas_necessarias - set(df.columns)
        if faltando:
            self.stdout.write(self.style.ERROR(
                f'A planilha precisa ter as colunas: Nome, Idade, Gênero, Série. '
                f'Faltando: {", ".join(sorted(faltando))}'
            ))
            return

        # Mapa case-insensitive: "3º ano" / "3º Ano" / "3º ANO" -> valor canônico "3º ano"
        series_validas = {valor.lower(): valor for valor, _ in Aluno.SERIE_CHOICES}

        criados = 0
        ja_existentes = 0
        erros = 0

        for index, row in df.iterrows():
            linha_numero = index + 2  # +2 = cabeçalho (linha 1) + índice começando em 0

            nome = str(row.get('Nome', '')).strip()
            if not nome or nome.lower() == 'nan':
                self.stdout.write(self.style.WARNING(f'Linha {linha_numero}: Nome ausente. Pulando.'))
                erros += 1
                continue

            if not self.REGEX_NOME.match(nome):
                self.stdout.write(self.style.ERROR(
                    f'Linha {linha_numero}: Nome "{nome}" contém caracteres inválidos (apenas letras são permitidas). Pulando.'
                ))
                erros += 1
                continue

            try:
                idade = int(float(row.get('Idade')))
                if idade < 0:
                    raise ValueError
            except (ValueError, TypeError):
                self.stdout.write(self.style.ERROR(
                    f'Linha {linha_numero}: Idade inválida ("{row.get("Idade")}"). Pulando.'
                ))
                erros += 1
                continue

            genero_bruto = str(row.get('Gênero', '')).strip().upper()
            genero = self.GENERO_MAP.get(genero_bruto)
            if not genero:
                self.stdout.write(self.style.ERROR(
                    f'Linha {linha_numero}: Gênero inválido ("{row.get("Gênero")}"). '
                    f'Use Masculino, Feminino ou Outro (ou M/F/O). Pulando.'
                ))
                erros += 1
                continue

            serie_bruta = str(row.get('Série', '')).strip()
            serie = series_validas.get(serie_bruta.lower())
            if not serie:
                self.stdout.write(self.style.ERROR(
                    f'Linha {linha_numero}: Série inválida ("{serie_bruta}"). '
                    f'Opções válidas: {", ".join(v for v, _ in Aluno.SERIE_CHOICES)}. Pulando.'
                ))
                erros += 1
                continue

            aluno, created = Aluno.objects.get_or_create(
                nome=nome,
                serie=serie,
                defaults={'idade': idade, 'genero': genero}
            )

            if created:
                criados += 1
                self.stdout.write(self.style.SUCCESS(f'Aluno criado: "{aluno.nome}" ({aluno.serie})'))
            else:
                ja_existentes += 1
                self.stdout.write(self.style.WARNING(
                    f'Linha {linha_numero}: Aluno "{nome}" já cadastrado na série "{serie}". Pulando.'
                ))

        self.stdout.write(self.style.SUCCESS('\nImportação concluída!'))
        self.stdout.write(f'Alunos criados: {criados}')
        self.stdout.write(f'Alunos já existentes (pulados): {ja_existentes}')
        self.stdout.write(self.style.ERROR(f'Linhas com erros: {erros}') if erros else 'Linhas com erros: 0')
