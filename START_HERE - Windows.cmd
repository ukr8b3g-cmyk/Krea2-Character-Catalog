@echo off
setlocal
title Krea2 Character Catalog
set "CATALOG_APP=%~dp0app"
if not exist "%CATALOG_APP%\tools\bootstrap.cmd" set "CATALOG_APP=%~dp0"
if not exist "%CATALOG_APP%\tools\bootstrap.cmd" (
  echo Catalog files are missing. Extract the complete catalog ZIP and keep the app folder beside this startup file. 1>&2
  "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -Command "if (!$env:CI -and !$env:KREA2_CATALOG_NO_PAUSE -and ![Console]::IsInputRedirected -and ![Console]::IsOutputRedirected) { [void](Read-Host 'Press Enter to close') }"
  exit /b 2
)
call "%CATALOG_APP%\tools\bootstrap.cmd" %*
exit /b %errorlevel%
