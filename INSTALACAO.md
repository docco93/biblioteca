# 🚀 Guia de Instalação - Sistema de Biblioteca

> Este projeto foi adaptado a partir do projeto original
> [lauraemmanuella/Biblioteca](https://github.com/lauraemmanuella/Biblioteca).

## Pré-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)
- Git (opcional, para clonar o repositório)

## Instalação Passo a Passo

> 💡 **Atalho para Windows:** depois de baixar o projeto e configurar o
> `.env` (passos 2 e 4 abaixo), você pode rodar o arquivo
> `configurar_inicial.bat` (dois cliques) para instalar as dependências,
> aplicar as migrações e criar o usuário administrador automaticamente —
> ele faz de uma vez os passos 3, 5 e 7. Depois é só usar o
> `iniciar_servidor.bat` (passo 8) sempre que quiser ligar o sistema.

### 1. Preparar o Ambiente

```bash
# Verificar versão do Python
python --version
# ou
python3 --version

# Atualizar pip
pip install --upgrade pip
```

### 2. Baixar o Projeto

```bash
# Se usando Git
git clone <url-do-repositorio>
cd Biblioteca

# Ou extrair o arquivo ZIP baixado
unzip Biblioteca.zip
cd Biblioteca
```

### 3. Instalar Dependências

```bash
# Instalar pacotes necessários
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente

```bash
# Copiar o arquivo de exemplo
cp .env.example .env
```

Abra o arquivo `.env` criado e gere uma chave secreta própria (não use a
mesma de outro projeto nem deixe a de exemplo em produção):
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```
Cole o valor gerado em `DJANGO_SECRET_KEY=` dentro do `.env`. Para rodar
localmente, pode deixar `DJANGO_DEBUG=True` e `DJANGO_ALLOWED_HOSTS=*`
como estão; ajuste isso apenas se for colocar o sistema em produção (veja
a seção "Configurações de Produção" mais abaixo).

### 5. Configurar Banco de Dados

```bash
# Aplicar migrações
python manage.py migrate
```

### 6. Popular com Dados de Exemplo (Opcional)

```bash
# Executar comando para criar dados de teste
python manage.py popular_dados
```

Este comando criará:
- 1 usuário administrador (admin/admin123)
- 3 alunos de exemplo (João Silva, Maria Santos, Pedro Costa — sem login)
- 5 títulos de livros com exemplares
- Alguns empréstimos de exemplo

### 7. Criar Superusuário (Alternativo)

```bash
# Se não usar o comando popular_dados
python manage.py createsuperuser
```

### 8. Executar o Servidor

```bash
# Iniciar servidor de desenvolvimento
python manage.py runserver

# Ou especificar porta
python manage.py runserver 8000
```

### 9. Acessar o Sistema

Abra seu navegador e acesse:
- **Sistema Principal**: http://localhost:8000
- **Admin Django**: http://localhost:8000/admin

## Iniciar o Servidor Automaticamente (Windows)

O projeto já vem com o arquivo `iniciar_servidor.bat` na pasta raiz (ao lado
do `manage.py`). Dando dois cliques nele, ele entra na pasta correta,
ativa o ambiente virtual (se existir um) e roda o servidor — não precisa
abrir o PowerShell/CMD manualmente.

Para o Windows rodar esse arquivo sozinho toda vez que o computador ligar:

**Opção mais simples — pasta Inicializar:**
1. Aperte `Win + R`, digite `shell:startup` e aperte Enter (abre a pasta de
   inicialização do Windows).
2. Clique com o botão direito no `iniciar_servidor.bat` → **Criar atalho**.
3. Arraste (ou recorte e cole) esse atalho para dentro da pasta que abriu no
   passo 1.

Pronto — a partir do próximo login no Windows, uma janela preta vai abrir
sozinha rodando o servidor. **Essa janela precisa continuar aberta** enquanto
o sistema estiver em uso (pode minimizar, mas não feche); fechá-la encerra
o servidor.

**Alternativa mais avançada — Agendador de Tarefas:** se quiser que o
servidor inicie mesmo antes de fazer login, ou rodar sem deixar a janela
visível, use o "Agendador de Tarefas" do Windows (`taskschd.msc`), criando
uma tarefa que executa o `iniciar_servidor.bat` no evento "Ao iniciar o
computador" ou "Ao fazer logon".

## Credenciais de Teste

### Administrador (único perfil com login)
- **Usuário**: admin
- **Senha**: admin123

Os alunos cadastrados pelo `popular_dados` não têm login — são apenas registros
(nome, idade, gênero, série) usados pelo administrador ao registrar empréstimos.

## Configurações Opcionais

### Sobre login e senha

O sistema não possui e-mail nem recuperação de senha por e-mail. Apenas o
administrador tem login e senha, e a redefinição de senha é feita diretamente
pelo Django Admin (`/admin/`) ou pelo comando `python manage.py changepassword <usuario>`.

### Notificações Automáticas

Para configurar notificações automáticas, adicione ao cron:

```bash
# Editar crontab
crontab -e

# Adicionar linha para executar diariamente às 9h
0 9 * * * /caminho/para/python /caminho/para/projeto/manage.py enviar_notificacoes
```

## Configurações de Produção

Se for colocar o sistema no ar (fora do seu computador, acessível por outras
pessoas), ajuste o arquivo `.env` antes:

```bash
DJANGO_SECRET_KEY=<uma-chave-forte-e-única-gerada-só-para-produção>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=meudominio.com,www.meudominio.com
```

- **DJANGO_SECRET_KEY**: gere uma chave nova (não reaproveite a de
  desenvolvimento) com `python -c "import secrets; print(secrets.token_urlsafe(50))"`.
- **DJANGO_DEBUG**: sempre `False` em produção — com `True`, o Django expõe
  detalhes internos do sistema (código, variáveis, configurações) em
  qualquer erro, o que é um risco de segurança.
- **DJANGO_ALLOWED_HOSTS**: liste os domínios reais separados por vírgula,
  nunca deixe `*` em produção.

Além disso, rode `python manage.py collectstatic` e sirva os arquivos
estáticos (CSS/JS) por um servidor apropriado (Nginx, WhiteNoise, etc.) —
o servidor de desenvolvimento (`runserver`) não deve ser usado em produção.

## Estrutura de Diretórios

```
biblioteca_sistema/
├── biblioteca/              # App principal
├── biblioteca_sistema/      # Configurações
├── templates/              # Templates HTML
├── static/                 # CSS, JS, imagens
├── media/                  # Uploads (QR codes)
├── db.sqlite3             # Banco de dados
├── manage.py              # Comando Django
├── README.md              # Documentação
└── INSTALACAO.md          # Este arquivo
```

## Comandos Úteis

```bash
# Verificar se há problemas
python manage.py check

# Criar migrações após mudanças nos models
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Acessar shell do Django
python manage.py shell

# Popular dados de exemplo
python manage.py popular_dados

# Enviar notificações manualmente
python manage.py enviar_notificacoes

# Coletar arquivos estáticos (produção)
python manage.py collectstatic
```

## Solução de Problemas

### Erro: "No module named 'django'" (ou 'PIL', 'qrcode')
```bash
pip install -r requirements.txt
```

### Erro ao instalar/importar pandas ("Import openpyxl failed", falha ao compilar pandas)
Isso costuma acontecer quando o Python instalado é muito recente (ex.: Python
3.13/3.14 recém-lançado) e ainda não existe um instalador pronto do pandas
para essa versão — o `pip` tenta compilar do zero e falha por falta do
Visual Studio Build Tools. Solução: instale sem fixar a versão, deixando o
`pip` escolher automaticamente uma versão compatível:
```bash
pip install openpyxl
pip install --upgrade pandas
```

### Erro de Migração
```bash
# Resetar migrações (cuidado: apaga dados)
rm biblioteca/migrations/0*.py
python manage.py makemigrations biblioteca
python manage.py migrate
```

### Porta já em uso
```bash
# Usar porta diferente
python manage.py runserver 8001
```

## Funcionalidades Principais

### Para Administradores (login obrigatório)
1. **Gestão de Títulos**: Cadastrar/editar livros
2. **Gestão de Exemplares**: Adicionar exemplares físicos
3. **Gestão de Alunos**: Cadastrar alunos (nome, idade, gênero, série)
4. **Controle de Empréstimos**: Registrar empréstimos escolhendo o aluno numa lista/busca, e processar devoluções
5. **Relatórios**: Visualizar estatísticas e relatórios

### Alunos
Não fazem login. São apenas um cadastro simples usado pelo administrador
para vincular os empréstimos.

## Importando dados em massa por planilha Excel

Em vez de cadastrar aluno ou título por vez manualmente pelo site, você
pode importar tudo de uma vez a partir de uma planilha `.xlsx`. O projeto
já vem com dois modelos prontos na pasta `planilhas_exemplo/`:
`cadastro_alunos.xlsx` e `cadastro_titulos.xlsx`. Abra-os, apague as linhas
de exemplo e preencha com seus dados reais, mantendo o cabeçalho.

> 💡 **Atalho para Windows:** depois de preencher as planilhas (mantendo
> os mesmos nomes de arquivo, dentro de `planilhas_exemplo/`), basta dar
> dois cliques em `importar_alunos.bat` ou `importar_titulos.bat` na pasta
> raiz do projeto — eles rodam o comando certo automaticamente, sem
> precisar abrir o terminal. Toda vez que atualizar os dados na planilha,
> é só rodar o `.bat` de novo.

### 1. Importar Alunos

A planilha `cadastro_alunos.xlsx` deve ter as colunas **Nome**, **Idade**,
**Gênero** e **Série** (em qualquer ordem, o comando identifica pelo nome
da coluna):

| Nome             | Idade | Gênero    | Série  |
|------------------|-------|-----------|--------|
| Ana Maria Costa  | 8     | Feminino  | 3º ano |
| João Pedro Souza | 9     | Masculino | 4º ano |

- **Nome**: apenas letras e espaços (sem números ou símbolos).
- **Gênero**: aceita `Masculino`/`Feminino`/`Outro` ou apenas `M`/`F`/`O`.
- **Série**: precisa ser uma destas opções (maiúsculas/minúsculas não importam):
  `Infantil 4`, `Infantil 5`, `1º ano`, `2º ano`, `3º ano`, `4º ano`, `5º ano`.

```bash
python manage.py importar_alunos "caminho/para/cadastro_alunos.xlsx"
```

Alunos com o mesmo nome **e** a mesma série de um já cadastrado são
ignorados (para não duplicar); se dois alunos reais tiverem nome e série
idênticos, cadastre o segundo manualmente com um sobrenome/diferencial.

### 2. Importar Títulos

A planilha `cadastro_titulos.xlsx` segue exatamente os campos da tela
"Cadastrar Título": cada linha é **um título** (uma obra), não um exemplar.

| Lombada | Título da Obra     | Título Original | Subtítulo | Autor                    | Editora | Ano  | Edição |
|---------|---------------------|------------------|-----------|--------------------------|---------|------|--------|
| PP-001  | O Pequeno Príncipe | Le Petit Prince  |           | Antoine de Saint-Exupéry | Agir    | 2015 | 1ª     |
| DC-001  | Dom Casmurro        |                  |           | Machado de Assis         | Ática   | 2020 |        |

- **Obrigatórios**: Lombada, Título da Obra, Autor, Editora, Ano.
- **Opcionais**: Título Original, Subtítulo, Edição.
- A **Lombada** precisa ser única — se já existir um título com a mesma
  lombada, a linha é pulada (avisando no terminal).

```bash
python manage.py importar_titulos "caminho/para/cadastro_titulos.xlsx"
```

Os exemplares (cópias físicas) de cada título continuam sendo cadastrados
pela tela do sistema, em Painel > Exemplares > Adicionar Exemplar.

### Dica geral

Se sua planilha tiver várias abas, use `--sheet "NomeDaAba"` (ou o número da
aba, começando em 0) em qualquer um dos dois comandos para indicar qual deve
ser lida; por padrão, ambos leem a primeira aba. Os dois comandos avisam
linha por linha se algo estiver inválido e pulam só a linha com problema —
o restante da planilha continua sendo importado normalmente.

## Próximos Passos

1. Acesse o sistema em http://localhost:8000
2. Faça login como administrador em /login/ com as credenciais de teste
3. Explore as funcionalidades no painel (/painel/)
4. Cadastre novos livros, exemplares e alunos
5. Teste o registro de empréstimos e devoluções

## Suporte

Para dúvidas ou problemas:
- Consulte o arquivo README.md
- Verifique os logs do Django
- Teste com dados de exemplo primeiro

**Sistema pronto para uso! 🎉**
