@echo off
:: ─────────────────────────────────────────────────────────────────
::  build.bat  —  Packages VikingMesh Processor into a Windows .exe
::  Run this once on a machine that has Python + pip installed.
::  The finished exe will appear in:  dist\VikingMeshProcessor\VikingMeshProcessor.exe
:: ─────────────────────────────────────────────────────────────────

echo.
echo [1/4] Installing / upgrading dependencies...
pip install pymeshlab trimesh pycollada pyinstaller --upgrade --quiet
if errorlevel 1 (
    echo ERROR: pip install failed. Make sure Python is in your PATH.
    pause
    exit /b 1
)

echo.
echo [2/4] Cleaning previous build artefacts...
if exist build                    rmdir /s /q build
if exist dist                     rmdir /s /q dist
if exist VikingMeshProcessor.spec del /q VikingMeshProcessor.spec

echo.
echo [3/4] Building executable with PyInstaller...
pyinstaller ^
    --name "VikingMeshProcessor" ^
    --onedir ^
    --windowed ^
    --hidden-import pymeshlab ^
    --hidden-import trimesh ^
    --hidden-import trimesh.exchange.export ^
    --hidden-import trimesh.exchange.gltf ^
    --hidden-import trimesh.exchange.load ^
    --hidden-import trimesh.exchange.dae ^
    --hidden-import collada ^
    --hidden-import collada.scene ^
    --hidden-import collada.material ^
    --hidden-import numpy ^
    vikingmesh_processor.py

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller failed. See output above for details.
    pause
    exit /b 1
)

echo.
echo [4/4] Done!
echo.
echo  Your app is ready at:
echo    dist\VikingMeshProcessor\VikingMeshProcessor.exe
echo.
echo  To distribute: zip the entire  dist\VikingMeshProcessor\  folder.
echo  Users do NOT need Python installed.
echo.
pause
