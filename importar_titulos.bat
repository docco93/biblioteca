@echo off
chcp 65001 >nul
REM ===================================================================
REM Importa titulos a partir da planilha planilhas_exemplo\cadastro_titulos.xlsx
REM Este arquivo deve ficar na PASTA RAIZ do projeto, ao lado do manage.py.
REM ===================================================================

cd /d %~dp0

echo ===================================================
echo       IMPORTACAO DE LIVROS - SISTEMA BIBLIOTECA
echo ===================================================
echo.

if not exist "manage.py" (
    echo ERRO: nao encontrei o arquivo manage.py nesta pasta.
    echo Verifique se este .bat esta na pasta raiz do projeto.
    pause
    exit /b 1
)

if not exist "planilhas_exemplo\cadastro_titulos.xlsx" (
    echo ERRO: nao encontrei a planilha planilhas_exemplo\cadastro_titulos.xlsx
    echo Verifique se o arquivo existe e se o nome esta correto.
    pause
    exit /b 1
)

REM Se existir uma pasta "venv" (ambiente virtual), ativa ela antes de rodar.
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo Iniciando a importacao da planilha de titulos...
echo.

python manage.py importar_titulos "planilhas_exemplo\cadastro_titulos.xlsx"

echo.
echo ===================================================
echo Importacao finalizada! Verifique os avisos acima.
echo ===================================================
pause
