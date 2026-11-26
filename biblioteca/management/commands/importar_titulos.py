#!/usr/bin/env python3
import os
import unicodedata
import pandas as pd
from django.core.management.base import BaseCommand
from biblioteca.models import Titulo


class Command(BaseCommand):
    help = (
        'Importa títulos de uma planilha Excel para o banco de dados. '
        'A planilha deve ter as colunas: Lombada, Título da Obra, Autor, Editora, Ano '
        '(e opcionalmente Título Original, Subtítulo, Edição).'
    )

    # Mapeia possíveis variações do nome da coluna (sem espaços/acentos/maiúsculas) -> nome padrão usado no código
    MAPA_COLUNAS = {
        'lombada': 'Lombada',
        'codigo da lombada': 'Lombada',
        'titulo da obra': 'Título da Obra',
        'titulo': 'Título da Obra',
        'autor': 'Autor',
        'titulo original': 'Título Original',
        'subtitulo': 'Subtítulo',
        'editora': 'Editora',
        'nome da editora': 'Editora',
        'ano': 'Ano',
        'ano de publicacao': 'Ano',
        'edicao': 'Edição',
    }

    def add_arguments(self, parser):
        parser.add_argument('caminho_planilha', type=str, help='O caminho para a planilha Excel a ser importada.')
        parser.add_argument(
            '--sheet',
            type=str,
            default=0,
            help='Nome ou índice da aba a ser lida (padrão: primeira aba).'
        )

    def _chave(self, nome_coluna):
        nome = str(nome_coluna).strip().lower()
        return unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('ASCII')

    def _normalizar_colunas(self, df):
        """Renomeia as colunas da planilha para os nomes padrão usados pelo comando,
        aceitando pequenas variações de espaço/acentuação/maiúsculas no cabeçalho."""
        mapa_normalizado = {}
        for coluna in df.columns:
            k = self._chave(coluna)
            if k in self.MAPA_COLUNAS:
                mapa_normalizado[coluna] = self.MAPA_COLUNAS[k]
        df = df.rename(columns=mapa_normalizado)
        # Segurança: se houver colunas duplicadas após a normalização, mantém a primeira
        df = df.loc[:, ~df.columns.duplicated()]
        return df

    @staticmethod
    def _limpar(valor):
        """Converte para string, remove espaços e trata 'nan'/'.0' do pandas."""
        valor = str(valor).strip()
        if valor.lower() == 'nan':
            return ''
        if valor.endswith('.0'):
            valor = valor[:-2]
        return valor

    def handle(self, *args, **kwargs):
        caminho_planilha = kwargs['caminho_planilha']
        sheet = kwargs['sheet']

        if not os.path.exists(caminho_planilha):
            self.stdout.write(self.style.ERROR(f'Arquivo não encontrado em: {caminho_planilha}'))
            return

        try:
            df = pd.read_excel(caminho_planilha, sheet_name=sheet).astype(str)
            df = self._normalizar_colunas(df)
            self.stdout.write(self.style.SUCCESS(f'Planilha "{os.path.basename(caminho_planilha)}" lida com sucesso.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao ler a planilha: {e}'))
            return

        colunas_obrigatorias = {'Lombada', 'Título da Obra', 'Autor', 'Editora', 'Ano'}
        faltando = colunas_obrigatorias - set(df.columns)
        if faltando:
            self.stdout.write(self.style.ERROR(
                f'A planilha precisa ter as colunas: Lombada, Título da Obra, Autor, Editora, Ano. '
                f'Faltando: {", ".join(sorted(faltando))}'
            ))
            return

        criados = 0
        ja_existentes = 0
        erros = 0

        for index, row in df.iterrows():
            linha_numero = index + 2  # +2 = cabeçalho (linha 1) + índice começando em 0

            lombada = self._limpar(row.get('Lombada', ''))
            titulo_da_obra = self._limpar(row.get('Título da Obra', ''))
            autor = self._limpar(row.get('Autor', ''))
            editora = self._limpar(row.get('Editora', ''))
            ano_str = self._limpar(row.get('Ano', '')).split('.')[0]

            if not lombada:
                self.stdout.write(self.style.ERROR(f'Linha {linha_numero}: Lombada ausente. Pulando.'))
                erros += 1
                continue

            if not titulo_da_obra:
                self.stdout.write(self.style.ERROR(f'Linha {linha_numero}: Título da Obra ausente. Pulando.'))
                erros += 1
                continue

            if not autor:
                self.stdout.write(self.style.ERROR(f'Linha {linha_numero}: Autor ausente. Pulando.'))
                erros += 1
                continue

            if not editora:
                self.stdout.write(self.style.ERROR(f'Linha {linha_numero}: Editora ausente. Pulando.'))
                erros += 1
                continue

            if not ano_str.isdigit() or int(ano_str) <= 1000:
                self.stdout.write(self.style.ERROR(f'Linha {linha_numero}: Ano inválido ("{row.get("Ano")}"). Pulando.'))
                erros += 1
                continue
            ano_publicacao = int(ano_str)

            titulo_original = self._limpar(row.get('Título Original', ''))
            subtitulo = self._limpar(row.get('Subtítulo', ''))
            edicao = self._limpar(row.get('Edição', ''))

            if Titulo.objects.filter(lombada=lombada).exists():
                ja_existentes += 1
                self.stdout.write(self.style.WARNING(
                    f'Linha {linha_numero}: já existe um título com a lombada "{lombada}". Pulando.'
                ))
                continue

            titulo = Titulo.objects.create(
                lombada=lombada,
                titulo_da_obra=titulo_da_obra,
                titulo_original=titulo_original,
                subtitulo=subtitulo,
                autor=autor,
                editora=editora,
                ano_publicacao=ano_publicacao,
                edicao=edicao,
            )
            criados += 1
            self.stdout.write(self.style.SUCCESS(f'Título criado: "{titulo.titulo_da_obra}" (lombada {titulo.lombada})'))

        self.stdout.write(self.style.SUCCESS('\nImportação concluída!'))
        self.stdout.write(f'Títulos criados: {criados}')
        self.stdout.write(f'Títulos já existentes (pulados): {ja_existentes}')
        self.stdout.write(self.style.ERROR(f'Linhas com erros: {erros}') if erros else 'Linhas com erros: 0')
