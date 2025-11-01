"""
Fieldnote Lite - 主程序
田野笔记管理与导出工具
"""
import sys
import os

# 修复 Qt 路径问题（必须在导入 PyQt6 之前）
if getattr(sys, 'frozen', False):
    # 运行在打包后的环境中
    bundle_dir = sys._MEIPASS
    os.environ['QT_MAC_WANTS_LAYER'] = '1'
    
    # 禁用 Qt 权限检查（防止崩溃）
    os.environ['QT_MAC_DISABLE_FOREGROUND_APPLICATION_TRANSFORM'] = '1'
    os.environ['QT_LOGGING_RULES'] = 'qt.qpa.permissions=false'
    
    # 确保 Qt 能找到插件
    plugin_path = os.path.join(bundle_dir, 'PyQt6', 'Qt6', 'plugins')
    if os.path.exists(plugin_path):
        os.environ['QT_PLUGIN_PATH'] = plugin_path
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(plugin_path, 'platforms')

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QLockFile, QDir
from gui import MainWindow


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("Fieldnote Lite")
    app.setOrganizationName("Linguistics Research")
    
    # 单实例检查：防止程序被多次启动
    # 创建锁文件在临时目录
    temp_dir = QDir.tempPath()
    lock_file_path = os.path.join(temp_dir, 'fieldnote_lite.lock')
    lock_file = QLockFile(lock_file_path)
    
    # 尝试获取锁
    if not lock_file.tryLock(100):
        # 如果无法获取锁，说明程序已经在运行
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Fieldnote Lite")
        msg.setText("程序已在运行")
        msg.setInformativeText("Fieldnote Lite 已经有一个实例在运行中。\n\n"
                              "请在任务栏或 Dock 中查找已打开的窗口。\n\n"
                              "如果确定没有其他实例在运行，请检查并删除锁文件：\n"
                              f"{lock_file_path}")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        sys.exit(1)
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    result = app.exec()
    
    # 退出时释放锁
    lock_file.unlock()
    
    sys.exit(result)


if __name__ == "__main__":
    main()

