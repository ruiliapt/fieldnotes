#!/bin/bash
# Fieldnote Lite - 修复版构建脚本
# 解决 macOS "quit unexpectedly" 问题

echo "=========================================="
echo "  Fieldnote Lite - 修复版构建"
echo "=========================================="
echo ""

# 检查 PyInstaller
if ! poetry run python -c "import PyInstaller" 2>/dev/null; then
    echo "安装 PyInstaller..."
    poetry add --group dev pyinstaller
fi

# 清理旧的构建
echo "清理旧的构建文件..."
rm -rf build dist *.spec

# 获取 Python 路径和依赖路径
PYTHON_PATH=$(poetry run python -c "import sys; print(sys.executable)")
SITE_PACKAGES=$(poetry run python -c "import site; print(site.getsitepackages()[0])")

echo ""
echo "Python 路径: $PYTHON_PATH"
echo "Site packages: $SITE_PACKAGES"
echo ""

# 创建 hook 文件来确保所有依赖都被包含
mkdir -p hooks
cat > hooks/hook-PyQt6.py << 'EOFHOOK'
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_dynamic_libs

datas, binaries, hiddenimports = collect_all('PyQt6')
datas += collect_data_files('PyQt6')
binaries += collect_dynamic_libs('PyQt6')

hiddenimports += [
    'PyQt6.sip',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
]
EOFHOOK

cat > hooks/hook-docx.py << 'EOFHOOK'
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('docx')
hiddenimports += [
    'docx.oxml',
    'docx.oxml.ns',
    'docx.oxml.shared',
    'docx.oxml.text',
    'docx.oxml.table',
    'lxml',
    'lxml._elementpath',
]
EOFHOOK

echo "已创建自定义 hooks"
echo ""

# 打包（修复 Qt 路径问题的版本）
echo "开始打包（修复版配置）..."

# 获取 PyQt6 的安装路径
PYQT6_PATH=$(poetry run python -c "import PyQt6; import os; print(os.path.dirname(PyQt6.__file__))")
echo "PyQt6 路径: $PYQT6_PATH"

# 检查 Qt 插件目录
QT_PLUGINS="$PYQT6_PATH/Qt6/plugins"
if [ -d "$QT_PLUGINS" ]; then
    echo "✅ 找到 Qt 插件目录: $QT_PLUGINS"
else
    echo "⚠️  Qt 插件目录不存在，可能会有问题"
fi

poetry run pyinstaller \
    --name="Fieldnote" \
    --windowed \
    --osx-bundle-identifier="com.linguistics.fieldnote" \
    --add-data="database.py:." \
    --add-data="gui.py:." \
    --add-data="exporter.py:." \
    --hidden-import=PyQt6 \
    --hidden-import=PyQt6.QtCore \
    --hidden-import=PyQt6.QtGui \
    --hidden-import=PyQt6.QtWidgets \
    --hidden-import=PyQt6.sip \
    --hidden-import=sip \
    --hidden-import=docx \
    --hidden-import=docx.oxml \
    --hidden-import=docx.oxml.ns \
    --hidden-import=docx.oxml.shared \
    --hidden-import=docx.oxml.text \
    --hidden-import=docx.oxml.xmlchemy \
    --hidden-import=docx.parts \
    --hidden-import=docx.parts.document \
    --hidden-import=lxml \
    --hidden-import=lxml._elementpath \
    --hidden-import=lxml.etree \
    --hidden-import=pandas \
    --hidden-import=numpy \
    --hidden-import=sqlite3 \
    --hidden-import=database \
    --hidden-import=gui \
    --hidden-import=exporter \
    --collect-all=PyQt6 \
    --collect-all=docx \
    --collect-submodules=PyQt6 \
    --collect-submodules=docx \
    --copy-metadata=PyQt6 \
    --copy-metadata=PyQt6-Qt6 \
    --additional-hooks-dir=hooks \
    --clean \
    --noconfirm \
    main.py

# 验证 Qt 插件是否被打包
echo ""
echo "验证打包结果..."
if [ -d "dist/Fieldnote.app/Contents/MacOS/PyQt6/Qt6/plugins" ]; then
    echo "✅ Qt 插件已打包"
    ls -la "dist/Fieldnote.app/Contents/MacOS/PyQt6/Qt6/plugins/"
else
    echo "⚠️  Qt 插件可能缺失"
fi

BUILD_EXIT=$?

echo ""
if [ $BUILD_EXIT -ne 0 ]; then
    echo "❌ 构建失败！"
    exit 1
fi

# 检查构建结果
if [ ! -d "dist/Fieldnote.app" ]; then
    echo "❌ 构建的 .app 不存在"
    exit 1
fi

echo "✅ 构建完成"
echo ""

# 测试启动（更详细）
echo "=========================================="
echo "  测试启动"
echo "=========================================="
echo ""
echo "尝试从终端运行以查看详细错误..."
echo ""

# 直接运行并捕获输出
./dist/Fieldnote.app/Contents/MacOS/Fieldnote 2>&1 &
TEST_PID=$!

sleep 5

if ps -p $TEST_PID > /dev/null 2>&1; then
    echo "✅ 程序正在运行（PID: $TEST_PID）"
    echo ""
    echo "现在尝试关闭..."
    kill $TEST_PID 2>/dev/null
    sleep 1
    
    if ps -p $TEST_PID > /dev/null 2>&1; then
        kill -9 $TEST_PID 2>/dev/null
    fi
    
    echo "✅ 测试通过！"
else
    echo "❌ 程序启动后立即退出"
    echo ""
    echo "请运行诊断脚本查看详细信息："
    echo "  ./scripts/debug_crash.sh"
    exit 1
fi

echo ""
echo "=========================================="
echo "  构建成功！"
echo "=========================================="
echo ""
echo "可执行文件: dist/Fieldnote.app"
echo ""
du -sh dist/Fieldnote.app
echo ""
echo "运行程序："
echo "  open dist/Fieldnote.app"
echo ""
echo "或从终端运行（查看调试信息）："
echo "  ./dist/Fieldnote.app/Contents/MacOS/Fieldnote"
echo ""
echo "打包为 ZIP："
echo "  cd dist && zip -r Fieldnote-v0.1.0-macOS.zip Fieldnote.app"
echo ""

