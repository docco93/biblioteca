# Sistema de Gestão de Biblioteca

Sistema web desenvolvido em Django para a **Biblioteca da Escola do Campo
Presidente Costa e Silva**, incluindo cadastro de livros, controle de
exemplares físicos e gestão de empréstimos/devoluções.

> Este projeto foi adaptado a partir do projeto original
> [lauraemmanuella/Biblioteca](https://github.com/lauraemmanuella/Biblioteca).

## 🚀 Funcionalidades

### Alunos (sem login)
- ✅ Cadastro simples pelo administrador: nome, idade, gênero e série
- ✅ Vinculados aos empréstimos registrados pelo administrador
- ✅ Suspensão automática em caso de atraso na devolução

### Para Administradores (login obrigatório)
- ✅ Painel administrativo completo
- ✅ Cadastro e gestão de títulos e exemplares
- ✅ Cadastro e gestão de alunos (nome, idade, gênero, série)
- ✅ Registro de empréstimos escolhendo o aluno numa lista/busca
- ✅ Controle de empréstimos e devoluções
- ✅ Relatórios e estatísticas
- ✅ Geração automática de QR Codes

### Regras de Negócio
- ✅ Máximo de 3 livros emprestados por aluno
- ✅ Prazo padrão de 30 dias para devolução
- ✅ Suspensão automática em caso de atraso
- ✅ QR Codes únicos para cada exemplar
- ✅ Nome do aluno aceita apenas letras (sem números ou símbolos)
- ✅ Série do aluno limitada a uma lista fixa (Infantil 4/5 e 1º a 5º ano)

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3.10+ + Django 5.2
- **Banco de Dados**: SQLite
- **Frontend**: HTML5, CSS3, Bootstrap 5.3
- **Bibliotecas**: 
  - Pillow (manipulação de imagens)
  - qrcode (geração de QR Codes)
  - pandas + openpyxl (importação de alunos/títulos por planilha Excel)
  - Chart.js (gráficos nos relatórios)

## 📋 Estrutura do Projeto

```
biblioteca_sistema/
├── biblioteca/                 # App principal
│   ├── models.py              # Modelos de dados (Usuario, Aluno, Titulo, Exemplar, Emprestimo)
│   ├── views.py               # Views e lógica de negócio
│   ├── forms.py               # Formulários
│   ├── urls.py                # URLs do app
│   ├── admin.py               # Configuração do Django Admin
│   ├── utils.py               # Utilitários e regras de negócio
│   └── management/            # Comandos personalizados
│       └── commands/
│           ├── enviar_notificacoes.py
│           ├── importar_alunos.py
│           ├── importar_titulos.py
│           └── popular_dados.py
├── templates/                 # Templates HTML
│   ├── base.html             # Template base
│   ├── biblioteca/           # Templates do app
│   └── registration/         # Templates de autenticação (administrador)
├── static/                   # Arquivos estáticos
├── media/                    # Uploads (QR Codes)
├── planilhas_exemplo/         # Modelos de planilha para importação em massa
│   ├── cadastro_alunos.xlsx
│   └── cadastro_titulos.xlsx
├── biblioteca_sistema/       # Configurações do projeto
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── configurar_inicial.bat     # Instala dependências, migra e cria o admin (rode 1x)
├── iniciar_servidor.bat       # Atalho para rodar o servidor no Windows (dê 2 cliques)
├── importar_alunos.bat        # Atalho para importar planilhas_exemplo/cadastro_alunos.xlsx
├── importar_titulos.bat       # Atalho para importar planilhas_exemplo/cadastro_titulos.xlsx
├── requirements.txt
├── .env.example              # Modelo de variáveis de ambiente (copie para .env)
├── .gitignore
└── README.md
```

## 🗄️ Modelos de Dados

### Usuario (administrador do sistema)
- Login, senha e nome completo (sem e-mail e sem recuperação de senha por e-mail)
- Status de administrador
- Não representa alunos — apenas quem opera o sistema (empréstimos/devoluções)
- Redefinição de senha é feita diretamente pelo Django Admin (não há fluxo de "esqueci minha senha")

### Aluno (cadastro simples, sem login)
- Nome, idade, gênero e série
- Data de suspensão (se aplicável)
- Vinculado aos empréstimos que o administrador registra

### Titulo (Obra)
- Lombada (código único), Título da Obra, Título Original e Subtítulo
- Autor, Editora, Edição e Ano de publicação

### Exemplar
- Referência ao título
- Código único do exemplar
- QR Code gerado automaticamente
- Status de disponibilidade
- Data de aquisição

### Emprestimo
- Aluno e exemplar
- Datas de empréstimo e devolução
- Previsão de devolução
- Cálculo automático de atrasos

## 🚀 Como Executar

### 1. Pré-requisitos
```bash
# Python 3.10+
python --version

# Pip atualizado
pip install --upgrade pip
```

### 2. Instalação
```bash
# Clone ou baixe o projeto
cd Biblioteca-main

# Crie e ative um ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Instale as dependências
pip install -r requirements.txt

# Execute as migrações
python manage.py migrate

# Popule com dados de exemplo (opcional)
python manage.py popular_dados

# Ou crie apenas um superusuário administrador
python manage.py createsuperuser
```

### 3. Executar o Servidor
```bash
python manage.py runserver
```

Acesse: http://localhost:8000

## 👥 Credenciais de Teste

Após executar `python manage.py popular_dados`:

### Administrador (único perfil com login)
- **Usuário**: admin
- **Senha**: admin123

Os alunos cadastrados por esse comando (João Silva, Maria Santos, Pedro Costa) **não têm login** — eles aparecem na lista de alunos do painel administrativo (`/painel/alunos/`) e podem ser escolhidos ao registrar um empréstimo.

## 📱 Funcionalidades Principais

### 1. Sistema de QR Codes
- Cada exemplar possui um QR Code único
- Escaneamento direciona para a página do exemplar

### 2. Gestão de Alunos
- Cadastro simples (nome, idade, gênero, série) em `/painel/alunos/`
- Suspensão manual ou automática (por atraso na devolução)

### 3. Empréstimos
- Registrados pelo administrador em `/painel/emprestimos/criar/`
- O aluno é escolhido numa lista/busca (não precisa de login)

### 4. Relatórios Administrativos
- Estatísticas gerais do sistema
- Livros mais emprestados
- Alunos mais ativos
- Empréstimos atrasados
- Gráficos interativos

### 5. Interface Responsiva
- Design adaptado para desktop, tablet e mobile
- Bootstrap 5.3 com tema customizado

## 🔧 Configurações Importantes

### Settings.py
```python
# Configurações de mídia (QR Codes)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Login (apenas administrador)
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/painel/'
LOGOUT_REDIRECT_URL = '/'
```

## 📊 Comandos Úteis

```bash
# Popular banco com dados de exemplo
python manage.py popular_dados

# Importar alunos a partir de planilha Excel
python manage.py importar_alunos "planilhas_exemplo/cadastro_alunos.xlsx"

# Importar títulos a partir de planilha Excel
python manage.py importar_titulos "planilhas_exemplo/cadastro_titulos.xlsx"

# Verificar empréstimos vencendo/atrasados
python manage.py enviar_notificacoes

# Acessar shell do Django
python manage.py shell

# Criar migrações
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Coletar arquivos estáticos (produção)
python manage.py collectstatic
```

Detalhes de como preencher cada planilha (colunas obrigatórias, opções
válidas de gênero/série, etc.) estão no `INSTALACAO.md`.

## 🔐 Segurança

- Login obrigatório apenas para o administrador (área `/painel/`)
- Validação de dados em formulários
- Proteção CSRF em todas as forms
- Sanitização de inputs

## 📈 Melhorias Futuras

- [ ] Sistema de reservas
- [ ] Renovação online de empréstimos
- [ ] Backup automático do banco
- [ ] Logs de auditoria

## 📞 Suporte

Para dúvidas ou suporte, entre em contato com a administração da
Biblioteca da Escola do Campo Presidente Costa e Silva.

---

**Desenvolvido com ❤️ usando Django e Bootstrap**
