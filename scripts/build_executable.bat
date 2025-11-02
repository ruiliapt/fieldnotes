@echo off
REM Fieldnotes Lite - 可执行文件构建脚本 (Windows)

echo ==========================================
echo   Fieldnotes Lite - 构建可执行文件
echo ==========================================
echo.

REM 检查并安装 PyInstaller
echo 检查 PyInstaller...
poetry run python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo 警告：PyInstaller 未找到，尝试安装...
    
    REM 在 CI 环境中使用 pip 直接安装
    if defined CI (
        echo CI 环境检测到，使用 pip 安装...
        poetry run pip install pyinstaller
    ) else (
        poetry add --group dev pyinstaller
    )
    
    REM 再次检查
    poetry run python -c "import PyInstaller" 2>nul
    if errorlevel 1 (
        echo 错误：PyInstaller 安装失败！
        exit /b 1
    )
    echo 成功：PyInstaller 安装成功
) else (
    echo 成功：PyInstaller 已安装
)

REM 清理旧的构建
echo 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

REM 打包
echo.
echo 开始打包...
REM 使用 python -m PyInstaller 而不是 pyinstaller 命令（更可靠）
poetry run python -m PyInstaller ^
    --name=Fieldnotes ^
    --windowed ^
    --add-data="README.md;." ^
    --hidden-import=PyQt6 ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=docx ^
    --hidden-import=pandas ^
    --hidden-import=sqlite3 ^
    --clean ^
    --noconfirm ^
    main.py

REM 检查结果
if exist "dist\Fieldnotes" (
    echo.
    echo ==========================================
    echo   构建成功！
    echo ==========================================
    echo.
    echo 可执行文件位于: dist\Fieldnotes\
    echo.
    echo 运行程序：
    echo   dist\Fieldnotes\Fieldnotes.exe
    echo.
) else (
    echo.
    echo 构建失败！请检查错误信息。
    exit /b 1
)

pause

