@echo off
setlocal
if defined KREA2_CATALOG_PYTHON goto specified
where py.exe >nul 2>nul
if errorlevel 1 goto checkpython
py.exe -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if not errorlevel 1 goto pylauncher
:checkpython
where python.exe >nul 2>nul
if not errorlevel 1 goto python
echo Python 3.10+ is required. Install Python from https://www.python.org/downloads/ and reopen the catalog.
set "catalog_exit=1"
goto finished
:specified
"%KREA2_CATALOG_PYTHON%" "%~dp0launch_catalog.py" %*
set "catalog_exit=%errorlevel%"
goto finished
:pylauncher
py.exe -3 "%~dp0launch_catalog.py" %*
set "catalog_exit=%errorlevel%"
goto finished
:python
python.exe "%~dp0launch_catalog.py" %*
set "catalog_exit=%errorlevel%"
:finished
if not "%catalog_exit%"=="0" if not defined KREA2_CATALOG_NO_PAUSE pause
exit /b %catalog_exit%
