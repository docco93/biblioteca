@echo off
chcp 65001 >nul
REM ===================================================================
REM Configuracao inicial do projeto Biblioteca.
REM Instala as dependencias, aplica as migracoes e cria o usuario
REM administrador (superuser) - SEM criar dados de exemplo (popular_dados).
REM Este arquivo deve ficar na PASTA RAIZ do projeto, ao lado do manage.py.
REM Rode este arquivo apenas UMA VEZ, na primeira instalacao.
REM ===================================================================

cd /d %~dp0

echo ============================================
echo  Configuracao inicial - Biblioteca
echo ============================================
echo.

if not exist "manage.py" (
    echo ERRO: nao encontrei o arquivo manage.py nesta pasta.
    echo Verifique se este .bat esta na pasta raiz do projeto.
    pause
    exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
    echo ERRO: Python nao foi encontrado no seu computador ^(ou nao esta no PATH^).
    echo Instale o Python em https://www.python.org/downloads/ e tente novamente.
    echo Durante a instalacao, marque a opcao "Add Python to PATH".
    pause
    exit /b 1
)

REM Se existir uma pasta "venv" (ambiente virtual), ativa ela antes de instalar.
if exist "venv\Scripts\activate.bat" (
    echo Ambiente virtual encontrado, ativando...
    call venv\Scripts\activate.bat
) else (
    echo Nenhum ambiente virtual encontrado, instalando no Python do sistema.
)

echo.
echo [1/3] Instalando dependencias (requirements.txt)...
echo.
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERRO ao instalar as dependencias. Verifique as mensagens acima.
    pause
    exit /b 1
)

echo.
echo [2/3] Aplicando migracoes do banco de dados...
echo.
python manage.py migrate
if errorlevel 1 (
    echo.
    echo ERRO ao aplicar as migracoes. Verifique as mensagens acima.
    pause
    exit /b 1
)

echo.
echo [3/3] Criando o usuario administrador...
echo A seguir, o Django vai pedir um nome de usuario e uma senha.
echo (Nao ha campo de e-mail neste sistema, por isso ele nao sera pedido.)
echo.
python manage.py createsuperuser
if errorlevel 1 (
    echo.
    echo Nao foi possivel criar o superusuario agora.
    echo Se a mensagem acima disser que o usuario ja existe, pode ignorar.
)

echo.
echo ============================================
echo  Configuracao concluida!
echo  Para iniciar o servidor, use o arquivo iniciar_servidor.bat
echo ============================================
pause
