@echo off
REM Script to create a deployable QGIS plugin zip package

echo ================================================
echo Creating QGIS Plugin Deployment Package
echo ================================================
echo.

REM Get version from metadata.txt
for /f "tokens=2 delims==" %%a in ('findstr "^version=" green_ampt_plugin\metadata.txt') do set VERSION=%%a
echo Plugin version: %VERSION%

REM Define output filename
set OUTPUT_FILE=green_ampt_plugin_v%VERSION%.zip
set TEMP_DIR=%TEMP%\green_ampt_plugin_build_%RANDOM%
set PACKAGE_DIR=%TEMP_DIR%\green_ampt_plugin

echo Temporary directory: %TEMP_DIR%
echo Output file: %OUTPUT_FILE%
echo.

REM Create package directory
mkdir "%PACKAGE_DIR%"

REM Copy plugin files
echo Copying plugin files...
xcopy /E /I /Q green_ampt_plugin "%PACKAGE_DIR%"

REM Copy green-ampt-estimation (core functionality)
echo Copying green-ampt-estimation core tool...
mkdir "%PACKAGE_DIR%\green_ampt_estimation"
xcopy /E /I /Q green-ampt-estimation\green_ampt_tool "%PACKAGE_DIR%\green_ampt_estimation\green_ampt_tool"
copy green-ampt-estimation\requirements.txt "%PACKAGE_DIR%\green_ampt_estimation\" >nul
copy green-ampt-estimation\LICENSE "%PACKAGE_DIR%\green_ampt_estimation\" >nul
copy green-ampt-estimation\README.md "%PACKAGE_DIR%\green_ampt_estimation\" >nul

REM Copy external dependencies (PySDA)
if exist "green-ampt-estimation\external\pysda" (
    echo Copying PySDA...
    mkdir "%PACKAGE_DIR%\green_ampt_estimation\external"
    xcopy /E /I /Q green-ampt-estimation\external\pysda "%PACKAGE_DIR%\green_ampt_estimation\external\pysda"
)

REM Clean up unnecessary files
echo Cleaning up unnecessary files...
del /S /Q "%PACKAGE_DIR%\*.pyc" >nul 2>&1
for /d /r "%PACKAGE_DIR%" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /d /r "%PACKAGE_DIR%" %%d in (.pytest_cache) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /S /Q "%PACKAGE_DIR%\.coverage" >nul 2>&1
del /S /Q "%PACKAGE_DIR%\*.log" >nul 2>&1
if exist "%PACKAGE_DIR%\green_ampt_estimation\green_ampt_tool\tests" rd /s /q "%PACKAGE_DIR%\green_ampt_estimation\green_ampt_tool\tests" 2>nul
if exist "%PACKAGE_DIR%\green_ampt_estimation\docs" rd /s /q "%PACKAGE_DIR%\green_ampt_estimation\docs" 2>nul
if exist "%PACKAGE_DIR%\green_ampt_estimation\examples" rd /s /q "%PACKAGE_DIR%\green_ampt_estimation\examples" 2>nul
if exist "%PACKAGE_DIR%\green_ampt_estimation\test_aoi" rd /s /q "%PACKAGE_DIR%\green_ampt_estimation\test_aoi" 2>nul
if exist "%PACKAGE_DIR%\green_ampt_estimation\scripts" rd /s /q "%PACKAGE_DIR%\green_ampt_estimation\scripts" 2>nul
if exist "%PACKAGE_DIR%\icon.svg" del "%PACKAGE_DIR%\icon.svg" 2>nul

REM Create the zip file (requires PowerShell)
echo Creating zip archive...
powershell -command "Compress-Archive -Path '%PACKAGE_DIR%' -DestinationPath '%CD%\%OUTPUT_FILE%' -Force"

REM Clean up
rd /s /q "%TEMP_DIR%"

REM Show package info
echo.
echo ================================================
echo Package created successfully!
echo ================================================
echo File: %OUTPUT_FILE%
echo.
echo To install:
echo   1. Open QGIS
echo   2. Go to Plugins - Manage and Install Plugins
echo   3. Click 'Install from ZIP'
echo   4. Select %OUTPUT_FILE%
echo   5. Enable 'Green-Ampt Parameter Generator'
echo.

pause
