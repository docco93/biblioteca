@echo off
chcp 65001 >nul
REM ===================================================================
REM Importa alunos a partir da planilha planilhas_exemplo\cadastro_alunos.xlsx
REM Este arquivo deve ficar na PASTA RAIZ do projeto, ao lado do manage.py.
REM ===================================================================

cd /d %~dp0

echo ===================================================
echo       IMPORTACAO DE ALUNOS - SISTEMA BIBLIOTECA
echo ===================================================
echo.

if not exist "manage.py" (
    echo ERRO: nao encontrei o arquivo manage.py nesta pasta.
    echo Verifique se este .bat esta na pasta raiz do projeto.
    pause
    exit /b 1
)

if not exist "planilhas_exemplo\cadastro_alunos.xlsx" (
    echo ERRO: nao encontrei a planilha planilhas_exemplo\cadastro_alunos.xlsx
    echo Verifique se o arquivo existe e se o nome esta correto.
    pause
    exit /b 1
)

REM Se existir uma pasta "venv" (ambiente virtual), ativa ela antes de rodar.
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo Iniciando a importacao da planilha de alunos...
echo.

python manage.py importar_alunos "planilhas_exemplo\cadastro_alunos.xlsx"

echo.
echo ===================================================
echo Importacao finalizada! Verifique os avisos acima.
echo ===================================================
pause
