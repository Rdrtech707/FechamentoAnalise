@echo off
REM Ativa o ambiente virtual
call "%~dp0venv\Scripts\activate.bat"

REM Executa o app.py
python app.py

REM Após finalizar o app.py, executa a interface gráfica
echo Iniciando interface gráfica...
python auditoria_gui.py

pause 