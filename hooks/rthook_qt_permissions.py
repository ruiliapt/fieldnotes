"""
PyInstaller runtime hook to disable Qt permission checks
This runs BEFORE any modules are imported
"""
import os
import sys

# 在任何 Qt 模块加载之前禁用权限检查
os.environ['QT_MAC_DISABLE_FOREGROUND_APPLICATION_TRANSFORM'] = '1'
os.environ['QT_LOGGING_RULES'] = 'qt.qpa.permissions=false'

# 尝试禁用 CoreLocation 框架（如果可能）
os.environ['QT_MAC_WANTS_LAYER'] = '1'

# 禁用所有 Qt 权限相关功能
os.environ['QT_QPA_NO_INPUT_METHOD'] = '1'

print("Qt permissions disabled via runtime hook", file=sys.stderr)

