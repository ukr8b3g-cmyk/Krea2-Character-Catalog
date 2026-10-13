@echo off
call "%~dp0tools\bootstrap.cmd" --editor %*
exit /b %errorlevel%
