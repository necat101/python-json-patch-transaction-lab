@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if %ERRORLEVEL%==0 set PY=python & goto :found
where python3 >nul 2>nul
if %ERRORLEVEL%==0 set PY=python3 & goto :found
where py >nul 2>nul
if %ERRORLEVEL%==0 set PY=py & goto :found
echo python not found (tried: python python3 py) 1>&2
exit /b 1

:found
set CMD=%1
if "%CMD%"=="" set CMD=run

if /I "%CMD%"=="run" goto :dorun
if /I "%CMD%"=="runner" goto :dorun
if /I "%CMD%"=="test" goto :dotest
if /I "%CMD%"=="tests" goto :dotest
if /I "%CMD%"=="unittest" goto :dotest
if /I "%CMD%"=="all" goto :doall
echo usage: %~nx0 [run ^| test ^| all] 1>&2
exit /b 2

:dorun
%PY% runner.py
exit /b %ERRORLEVEL%

:dotest
%PY% -m unittest test_independent -v
exit /b %ERRORLEVEL%

:doall
%PY% runner.py
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
%PY% -m unittest test_independent -q
exit /b %ERRORLEVEL%
