@echo off
echo Installing Bluff Revit Add-in...

REM Get the Revit add-ins directory
set "ADDIN_DIR=%APPDATA%\Autodesk\Revit\Addins\2022"

REM Create directory if it doesn't exist
if not exist "%ADDIN_DIR%" (
    echo Creating add-ins directory: %ADDIN_DIR%
    mkdir "%ADDIN_DIR%"
)

REM Copy files
echo Copying Bluff.addin...
copy "Bluff.addin" "%ADDIN_DIR%\"

echo Copying Bluff.dll...
copy "Source\Bluff\bin\Debug\Bluff.dll" "%ADDIN_DIR%\"

echo Copying cone_data.json...
copy "cone_data.json" "%ADDIN_DIR%\"

echo.
echo Installation complete!
echo.
echo Next steps:
echo 1. Load a sphere family into your Revit project
echo 2. Restart Revit
echo 3. Go to Add-Ins tab and click "Bluff"
echo.
echo Add-in files installed to: %ADDIN_DIR%
pause

