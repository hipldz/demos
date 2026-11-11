@echo off
setlocal EnableExtensions

rem ==================== 配置区 ====================
set "SEARCH_ROOT=%USERPROFILE%\.vscode\extensions"
set "DIR_PATTERN=openai.chatgpt-*-win32-x64"
set "EXE_REL_PATH=bin\windows-x86_64\codex-command-runner.exe"
set "APP_NAME=codex-command-runner"
rem ===============================================

set "APP="

rem 按修改时间倒序查找，优先使用最新安装的扩展目录
for /f "delims=" %%D in ('
    dir /b /ad /o-d "%SEARCH_ROOT%\%DIR_PATTERN%" 2^>nul
') do (
    set "APP=%SEARCH_ROOT%\%%D\%EXE_REL_PATH%"
    goto :APP_FOUND
)

echo [ERROR] %APP_NAME% installation folder was not found.
echo Search path: %SEARCH_ROOT%\%DIR_PATTERN%
pause
exit /b 1

:APP_FOUND

if not exist "%APP%" (
    echo [ERROR] %APP_NAME% executable was not found.
    echo Executable path: %APP%
    pause
    exit /b 1
)

"%APP%" %*
exit /b %ERRORLEVEL%