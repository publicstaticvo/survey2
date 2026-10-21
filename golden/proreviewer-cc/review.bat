@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PDF_DIR=%~1"
if "%PDF_DIR%"=="" set "PDF_DIR=%SCRIPT_DIR%..\review_pdfs\development_set"
set "LOG_DIR=proreviewer_logs"
set "CLAUDE_BIN=claude"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

set /a SUCCESS=0
set /a FAIL=0
set /a TOTAL=0

for %%F in ("%PDF_DIR%\*.pdf") do (
    set /a TOTAL+=1

    set "ABS_PDF=%%~fF"
    set "BASE=%%~nF"
    set "LOG=!LOG_DIR!\!BASE!.log"

    echo ==== Start: !ABS_PDF!
    echo      Log: !LOG!

    call %CLAUDE_BIN% -p "/proreviewer !ABS_PDF!" --dangerously-skip-permissions > "!LOG!" 2>&1

    if errorlevel 1 (
        echo ==== Fail: !ABS_PDF! ^(Detail: !LOG!^)
        set /a FAIL+=1
    ) else (
        echo ==== Finish: !ABS_PDF!
        set /a SUCCESS+=1
    )
)

if %TOTAL%==0 (
    echo No PDF in %PDF_DIR%
    exit /b 0
)

echo.
echo Finish: Success %SUCCESS% Fail %FAIL% 

if %FAIL% gtr 0 exit /b 1
endlocal