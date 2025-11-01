#!/bin/bash
# Fieldnote Lite - 崩溃诊断脚本

echo "=========================================="
echo "  Fieldnote Lite - 崩溃诊断工具"
echo "=========================================="
echo ""

APP_PATH="dist/Fieldnote.app"

if [ ! -d "$APP_PATH" ]; then
    echo "❌ 找不到 $APP_PATH"
    echo "请先运行: make build-exe"
    exit 1
fi

echo "📋 诊断步骤："
echo ""

# 1. 检查可执行文件
echo "1️⃣  检查可执行文件..."
EXECUTABLE="$APP_PATH/Contents/MacOS/Fieldnote"
if [ -f "$EXECUTABLE" ]; then
    echo "   ✅ 可执行文件存在"
    echo "   位置: $EXECUTABLE"
    ls -lh "$EXECUTABLE"
else
    echo "   ❌ 可执行文件不存在"
    exit 1
fi

echo ""

# 2. 尝试直接运行并查看错误
echo "2️⃣  尝试从终端运行（查看详细错误）..."
echo "   命令: $EXECUTABLE"
echo ""
echo "   --- 输出开始 ---"
"$EXECUTABLE" 2>&1
EXIT_CODE=$?
echo "   --- 输出结束 ---"
echo ""
echo "   退出码: $EXIT_CODE"

if [ $EXIT_CODE -eq 0 ]; then
    echo "   ✅ 程序正常退出"
else
    echo "   ❌ 程序异常退出"
fi

echo ""

# 3. 检查系统日志
echo "3️⃣  检查系统崩溃日志..."
CRASH_LOG=$(ls -t ~/Library/Logs/DiagnosticReports/Fieldnote* 2>/dev/null | head -1)

if [ -n "$CRASH_LOG" ]; then
    echo "   找到崩溃日志: $CRASH_LOG"
    echo ""
    echo "   --- 关键信息 ---"
    grep -A 5 "Exception Type:" "$CRASH_LOG" 2>/dev/null || echo "   (无法解析)"
    grep -A 5 "Termination Reason:" "$CRASH_LOG" 2>/dev/null || echo "   (无)"
    echo ""
    echo "   完整日志位置: $CRASH_LOG"
else
    echo "   未找到崩溃日志"
fi

echo ""

# 4. 检查依赖
echo "4️⃣  检查依赖库..."
FRAMEWORKS_DIR="$APP_PATH/Contents/Frameworks"
if [ -d "$FRAMEWORKS_DIR" ]; then
    echo "   Frameworks 目录存在"
    echo "   包含文件数: $(find "$FRAMEWORKS_DIR" -type f | wc -l)"
else
    echo "   ⚠️  Frameworks 目录不存在"
fi

echo ""

# 5. 检查 Python 库
echo "5️⃣  检查 Python 库..."
PYTHON_LIB="$APP_PATH/Contents/MacOS"
if [ -d "$PYTHON_LIB" ]; then
    echo "   查找 PyQt6..."
    if find "$PYTHON_LIB" -name "*PyQt6*" | grep -q .; then
        echo "   ✅ 找到 PyQt6"
    else
        echo "   ❌ 未找到 PyQt6"
    fi
    
    echo "   查找 python-docx..."
    if find "$PYTHON_LIB" -name "*docx*" | grep -q .; then
        echo "   ✅ 找到 python-docx"
    else
        echo "   ❌ 未找到 python-docx"
    fi
fi

echo ""

# 6. 推荐解决方案
echo "=========================================="
echo "  💡 可能的解决方案"
echo "=========================================="
echo ""
echo "方案 1: 重新构建（添加更多依赖）"
echo "   $ ./scripts/build_executable_fixed.sh"
echo ""
echo "方案 2: 从源码运行"
echo "   $ poetry run python main.py"
echo ""
echo "方案 3: 查看完整崩溃报告"
if [ -n "$CRASH_LOG" ]; then
    echo "   $ open '$CRASH_LOG'"
else
    echo "   $ open ~/Library/Logs/DiagnosticReports/"
fi
echo ""
echo "方案 4: 检查控制台日志"
echo "   打开\"控制台.app\" → 搜索 \"Fieldnote\""
echo ""

