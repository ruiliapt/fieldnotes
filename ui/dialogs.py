"""对话框混入 - DialogsMixin"""
import os
import logging
from datetime import datetime

from PyQt6.QtWidgets import QMessageBox, QDialog
from PyQt6.QtGui import QTextDocument
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter

logger = logging.getLogger(__name__)


class DialogsMixin:
    """Mixin for dialog-related operations (about, help, backup, print, etc.)."""

    def show_about_dialog(self):
        """显示关于对话框"""
        from gui import AboutDialog
        dialog = AboutDialog(self)
        dialog.exec()

    def show_shortcut_help(self):
        """显示快捷键帮助对话框"""
        from gui import ShortcutHelpDialog
        dialog = ShortcutHelpDialog(self)
        dialog.exec()

    def open_duplicate_detection(self):
        """打开去重检测对话框"""
        from gui import DuplicateDetectionDialog
        dialog = DuplicateDetectionDialog(self, self.db, self.theme_manager)
        dialog.exec()
        self.refresh_table()

    def open_font_settings(self):
        """打开字体设置对话框"""
        from gui import FontSettingsDialog
        dialog = FontSettingsDialog(self, self.font_config)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.font_config = dialog.get_config()
            self.save_font_config()
            self.apply_fonts()
            QMessageBox.information(self, "成功", "字体设置已应用！")

    def manual_backup(self):
        """手动备份数据库"""
        try:
            backup_path = self.db.create_backup()
            QMessageBox.information(
                self, "备份成功",
                f"数据库已备份到:\n{backup_path}"
            )
            self.statusBar().showMessage("数据库备份完成", 3000)
        except Exception as e:
            logger.error("手动备份失败: %s", e)
            QMessageBox.critical(self, "备份失败", f"备份过程中发生错误:\n{str(e)}")

    def auto_backup_on_startup(self):
        """启动时自动备份（每天最多一次）"""
        backup_dir = os.path.join(os.path.expanduser("~"), ".fieldnote", "backups")
        today = datetime.now().strftime("%Y%m%d")
        # 检查今日是否已备份
        if os.path.isdir(backup_dir):
            import glob as glob_std
            today_backups = glob_std.glob(os.path.join(backup_dir, f"corpus_{today}_*.db"))
            if today_backups:
                return  # 今日已有备份
        try:
            backup_path = self.db.create_backup()
            self.statusBar().showMessage(f"自动备份完成: {os.path.basename(backup_path)}", 5000)
            logger.info("启动自动备份完成: %s", backup_path)
        except Exception as e:
            logger.error("启动自动备份失败: %s", e)

    def check_database_integrity(self):
        """数据库完整性检查"""
        is_ok, message = self.db.check_integrity()
        if is_ok:
            QMessageBox.information(self, "完整性检查", message)
        else:
            QMessageBox.warning(self, "完整性检查", message)

    def print_current_tab(self):
        """打印当前Tab的语料"""
        entry_type = self.get_current_entry_type()
        entries = self.db.get_entries_by_type(entry_type)

        if not entries:
            QMessageBox.warning(self, "提示", "当前Tab没有可打印的语料！")
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle("打印语料")

        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            # 生成 HTML 表格
            html = self._build_print_html(entries, entry_type)
            doc = QTextDocument()
            doc.setHtml(html)
            doc.print_(printer)
            logger.info("打印完成: %d 条 %s 类型语料", len(entries), entry_type)
            self.statusBar().showMessage(f"打印完成: {len(entries)} 条", 3000)

    def _build_print_html(self, entries, entry_type: str) -> str:
        """构建打印用的 HTML 表格"""
        type_labels = {"word": "单词", "sentence": "单句", "discourse": "语篇", "dialogue": "对话"}
        type_label = type_labels.get(entry_type, entry_type)

        rows_html = ""
        for entry in entries:
            rows_html += "<tr>"
            rows_html += f"<td>{entry.get('example_id', '') or ''}</td>"
            rows_html += f"<td>{entry.get('source_text', '') or ''}</td>"
            rows_html += f"<td>{entry.get('gloss', '') or ''}</td>"
            rows_html += f"<td>{entry.get('translation', '') or ''}</td>"
            rows_html += f"<td>{entry.get('notes', '') or ''}</td>"
            rows_html += f"<td>{entry.get('tags', '') or ''}</td>"
            rows_html += "</tr>"

        html = f"""
        <html><head><meta charset="utf-8">
        <style>
            body {{ font-family: serif; font-size: 10pt; }}
            h2 {{ text-align: center; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #333; padding: 4px 6px; text-align: left; font-size: 9pt; }}
            th {{ background-color: #eee; font-weight: bold; }}
        </style></head><body>
        <h2>Fieldnotes Lite - {type_label}语料</h2>
        <p>共 {len(entries)} 条 | 打印时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <table>
        <tr><th>编号</th><th>原文</th><th>词汇分解</th><th>翻译</th><th>备注</th><th>标签</th></tr>
        {rows_html}
        </table></body></html>
        """
        return html
