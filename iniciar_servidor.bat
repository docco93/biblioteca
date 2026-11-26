@echo off
chcp 65001 >nul
REM ===================================================================
REM Inicia o servidor da Biblioteca (Django).
REM Este arquivo deve ficar na PASTA RAIZ do projeto, ao lado do manage.py.
REM ===================================================================

REM Muda para a pasta onde este arquivo .bat está salvo,
REM não importa de onde ele seja executado (ex: pela pasta Startup do Windows).
cd /d %~dp0

echo Iniciando o servidor da Biblioteca...
echo Pasta do projeto: %cd%
echo.

REM Se existir uma pasta "venv" (ambiente virtual), ativa ela antes de rodar.
if exist "venv\Scripts\activate.bat" (
    echo Ativando ambiente virtual...
    call venv\Scripts\activate.bat
) else (
    echo Nenhum ambiente virtual encontrado, usando o Python do sistema.
)

echo.
echo Para acessar o sistema, abra o navegador em: http://localhost:8000
echo Para parar o servidor, feche esta janela ou aperte Ctrl+C.
echo.

python manage.py runserver

REM Se o servidor parar ou der erro, mantém a janela aberta para você ler a mensagem.
echo.
echo O servidor foi encerrado.
pause
