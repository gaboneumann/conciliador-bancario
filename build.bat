@echo off
echo Construyendo ConciliadorBancario.exe...
pyinstaller conciliador_bancario.spec --clean
echo.
echo Listo. El ejecutable esta en: dist\ConciliadorBancario.exe
pause