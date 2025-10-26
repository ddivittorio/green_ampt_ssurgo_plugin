@echo off
REM Installation script for Green-Ampt Parameter Generator QGIS Plugin (Windows)

echo ===================================
echo Green-Ampt Plugin Installation
echo ===================================
echo.

set "QGIS_PLUGINS_DIR=%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins"

echo Target directory: %QGIS_PLUGINS_DIR%
echo.

REM Check if directory exists
if not exist "%QGIS_PLUGINS_DIR%" (
    echo Creating plugins directory...
    mkdir "%QGIS_PLUGINS_DIR%"
)

REM Initialize submodules
echo Initializing git submodules...
git submodule update --init --recursive

REM Copy plugin
echo Installing plugin...
set "PLUGIN_NAME=green_ampt_plugin"
set "TARGET_DIR=%QGIS_PLUGINS_DIR%\%PLUGIN_NAME%"

if exist "%TARGET_DIR%" (
    echo Warning: Plugin already exists at %TARGET_DIR%
    set /p REPLY="Do you want to overwrite it? (y/n) "
    if /i not "%REPLY%"=="y" (
        echo Installation cancelled.
        exit /b 1
    )
    rmdir /s /q "%TARGET_DIR%"
)

xcopy /E /I "%PLUGIN_NAME%" "%QGIS_PLUGINS_DIR%\%PLUGIN_NAME%"

echo.
echo ===================================
echo Installation Complete!
echo ===================================
echo.
echo Next steps:
echo 1. Start or restart QGIS
echo 2. Go to Plugins - Manage and Install Plugins
echo 3. Enable 'Green-Ampt Parameter Generator'
echo 4. Find the algorithm in Processing Toolbox
echo.

pause
