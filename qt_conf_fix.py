"""
QtCore 路径修复脚本
在 PyInstaller 打包时使用，确保 Qt 能找到正确的路径
"""
import os
import sys

def create_qt_conf():
    """创建 qt.conf 文件来指定 Qt 插件路径"""
    if getattr(sys, 'frozen', False):
        # 运行在打包后的环境中
        bundle_dir = sys._MEIPASS
    else:
        # 开发环境
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 设置 Qt 插件路径环境变量
    os.environ['QT_PLUGIN_PATH'] = os.path.join(bundle_dir, 'PyQt6', 'Qt6', 'plugins')
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(bundle_dir, 'PyQt6', 'Qt6', 'plugins', 'platforms')
    
    # 禁用 Qt 的自动路径查找
    os.environ['QT_MAC_WANTS_LAYER'] = '1'
    
    return bundle_dir

# 在导入 PyQt6 之前调用
create_qt_conf()

