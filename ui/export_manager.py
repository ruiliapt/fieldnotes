"""导出管理混入 - ExportManagerMixin"""
import csv
import json

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QTableWidget, QMessageBox, QFileDialog,
    QCheckBox, QComboBox, QGroupBox, QFormLayout, QDialog,
    QApplication
)

from exporter import TextFormatter
from ui.widgets import _get_monospace_font


class ExportManagerMixin:
    """Mixin for export-related operations."""

    def create_export_tab(self):
        """创建导出标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # 导出选项
        export_group = QGroupBox("导出选项")
        export_layout = QVBoxLayout()
        export_group.setLayout(export_layout)

        self.export_all_radio = QCheckBox("导出所有语料")
        self.export_all_radio.setChecked(True)
        export_layout.addWidget(self.export_all_radio)

        self.export_selected_radio = QCheckBox("仅导出搜索结果")
        export_layout.addWidget(self.export_selected_radio)

        # 类型选择
        type_select_layout = QHBoxLayout()
        type_select_layout.addWidget(QLabel("数据类型:"))
        self.export_type_combo = QComboBox()
        self.export_type_combo.addItems(
            ["全部类型", "单词", "单句", "语篇", "对话"]
        )
        type_select_layout.addWidget(self.export_type_combo)
        export_layout.addLayout(type_select_layout)

        # 分组选项
        self.export_group_by_checkbox = QCheckBox("按语篇/对话分组导出")
        self.export_group_by_checkbox.setChecked(False)
        self.export_group_by_checkbox.setToolTip("语篇和对话数据将按照其分组进行归类导出")
        export_layout.addWidget(self.export_group_by_checkbox)

        layout.addWidget(export_group)

        # 格式选项
        format_group = QGroupBox("格式设置")
        format_layout = QFormLayout()
        format_group.setLayout(format_layout)

        self.show_numbering_checkbox = QCheckBox()
        self.show_numbering_checkbox.setChecked(True)
        format_layout.addRow("显示编号:", self.show_numbering_checkbox)

        self.include_chinese_checkbox = QCheckBox()
        self.include_chinese_checkbox.setChecked(False)
        self.include_chinese_checkbox.setToolTip("导出时包含原文(汉字)、词汇分解(汉字)、翻译(汉字)字段")
        format_layout.addRow("包含汉字注释:", self.include_chinese_checkbox)

        layout.addWidget(format_group)

        # 导出按钮区域
        button_layout = QHBoxLayout()

        text_export_btn = QPushButton("生成对齐文本（可复制到Word）")
        text_export_btn.clicked.connect(self.generate_formatted_text)
        text_export_btn.setProperty('cssClass', 'accent')
        button_layout.addWidget(text_export_btn)

        word_export_btn = QPushButton("导出到Word文档")
        word_export_btn.clicked.connect(self.export_to_word)
        button_layout.addWidget(word_export_btn)

        csv_export_btn = QPushButton("导出CSV")
        csv_export_btn.clicked.connect(self.export_to_csv)
        button_layout.addWidget(csv_export_btn)

        json_export_btn = QPushButton("导出JSON")
        json_export_btn.clicked.connect(self.export_to_json)
        button_layout.addWidget(json_export_btn)

        layout.addLayout(button_layout)

        # 格式化文本显示区域
        text_display_group = QGroupBox("格式化文本（可直接复制）")
        text_display_layout = QVBoxLayout()
        text_display_group.setLayout(text_display_layout)

        self.formatted_text_display = QTextEdit()
        self.formatted_text_display.setReadOnly(True)
        self.formatted_text_display.setMinimumHeight(400)
        self.formatted_text_display.setFont(_get_monospace_font(11))
        text_display_layout.addWidget(self.formatted_text_display)

        # 复制按钮
        copy_btn = QPushButton("复制到剪贴板")
        copy_btn.clicked.connect(self.copy_formatted_text)
        text_display_layout.addWidget(copy_btn)

        layout.addWidget(text_display_group)

        return widget

    def _get_export_entries(self):
        """获取要导出的数据（根据类型筛选）"""
        from gui import COL_ID

        type_map = {
            "全部类型": None,
            "单词": "word",
            "单句": "sentence",
            "语篇": "discourse",
            "对话": "dialogue"
        }

        selected_type = type_map[self.export_type_combo.currentText()]

        if self.export_selected_radio.isChecked() and self.search_table.rowCount() > 0:
            entries = []
            for row in range(self.search_table.rowCount()):
                entry_id = int(self.search_table.item(row, COL_ID).text())
                entry = self.db.get_entry(entry_id)
                if entry:
                    if selected_type is None or entry.get('entry_type') == selected_type:
                        entries.append(entry)
        else:
            if selected_type is None:
                entries = self.db.get_all_entries()
            else:
                entries = self.db.get_entries_by_type(selected_type)

        return entries

    def generate_formatted_text(self):
        """生成格式化文本"""
        entries = self._get_export_entries()

        if not entries:
            QMessageBox.warning(self, "提示", "没有可导出的语料！")
            return

        show_numbering = self.show_numbering_checkbox.isChecked()
        include_chinese = self.include_chinese_checkbox.isChecked()
        group_by = self.export_group_by_checkbox.isChecked()

        if group_by:
            formatted_text = self._format_entries_by_group(entries, show_numbering, include_chinese)
        else:
            formatted_text = TextFormatter.format_entries(entries, show_numbering,
                                                         include_chinese=include_chinese)

        self.formatted_text_display.setPlainText(formatted_text)

        self.statusBar().showMessage(f"已生成 {len(entries)} 条语料的格式化文本", 3000)
        QMessageBox.information(
            self, "生成成功",
            f"已生成 {len(entries)} 条语料的格式化文本！\n\n"
            "文本已按词对齐，可以直接复制到Word或其他文档。\n"
            "建议在Word中使用等宽字体（如Courier New）以保持对齐。"
        )

    def _format_entries_by_group(self, entries, show_numbering=True, include_chinese=False):
        """按分组格式化输出"""
        groups = {}
        ungrouped = []

        for entry in entries:
            group_id = entry.get('group_id', '')
            if group_id:
                if group_id not in groups:
                    groups[group_id] = {
                        'name': entry.get('group_name', group_id),
                        'type': entry.get('entry_type', 'sentence'),
                        'entries': []
                    }
                groups[group_id]['entries'].append(entry)
            else:
                ungrouped.append(entry)

        lines = []

        for group_id in sorted(groups.keys()):
            group = groups[group_id]
            type_label = {"discourse": "语篇", "dialogue": "对话"}.get(group['type'], "分组")

            lines.append("=" * 60)
            lines.append(f"{type_label}: {group['name']} ({group_id})")
            lines.append(f"共 {len(group['entries'])} 句")
            lines.append("=" * 60)
            lines.append("")

            group_text = TextFormatter.format_entries(
                group['entries'],
                show_numbering,
                include_chinese=include_chinese
            )
            lines.append(group_text)
            lines.append("")

        if ungrouped:
            lines.append("=" * 60)
            lines.append(f"未分组数据 (共 {len(ungrouped)} 条)")
            lines.append("=" * 60)
            lines.append("")
            ungrouped_text = TextFormatter.format_entries(
                ungrouped,
                show_numbering,
                include_chinese=include_chinese
            )
            lines.append(ungrouped_text)

        return "\n".join(lines)

    def copy_formatted_text(self):
        """复制格式化文本到剪贴板"""
        text = self.formatted_text_display.toPlainText()
        if not text:
            QMessageBox.warning(self, "提示", "请先生成格式化文本！")
            return

        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "复制成功", "格式化文本已复制到剪贴板！")
        self.statusBar().showMessage("已复制到剪贴板", 3000)

    def export_to_word(self):
        """导出到Word文档"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存Word文档", "", "Word Documents (*.docx)"
        )

        if not file_path:
            return

        entries = self._get_export_entries()

        if not entries:
            QMessageBox.warning(self, "提示", "没有可导出的语料！")
            return

        show_numbering = self.show_numbering_checkbox.isChecked()
        include_chinese = self.include_chinese_checkbox.isChecked()
        group_by = self.export_group_by_checkbox.isChecked()

        if group_by:
            reply = QMessageBox.question(
                self, "分组导出",
                "Word导出暂不支持分组显示，将按普通方式导出所有数据。\n\n"
                "建议使用'生成对齐文本'功能以查看分组效果。\n\n"
                "是否继续导出到Word？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        try:
            success = self.exporter.export(
                entries, file_path,
                table_width=5.0,
                font_size=10,
                line_spacing=1.15,
                show_numbering=show_numbering,
                entries_per_page=10,
                include_chinese=include_chinese,
                font_config=self.font_config
            )

            if success:
                QMessageBox.information(
                    self, "导出成功",
                    f"成功导出 {len(entries)} 条语料到:\n{file_path}"
                )
                self.statusBar().showMessage(f"导出成功: {len(entries)} 条", 3000)
            else:
                QMessageBox.critical(self, "导出失败", "导出过程中发生错误！")

        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"错误: {str(e)}")

    def _get_selected_entries(self):
        """获取选中的语料"""
        from gui import COL_ID
        tab = self._get_current_tab()
        if not tab:
            return []

        data_table = tab.data_table
        selected_rows = data_table.selectionModel().selectedRows()
        if not selected_rows:
            return []

        entries = []
        for index in selected_rows:
            row = index.row()
            entry_id = int(data_table.item(row, COL_ID).text())
            entry = self.db.get_entry(entry_id)
            if entry:
                entries.append(entry)
        return entries

    def quick_export_text(self):
        """快速导出选中语料为文本"""
        entries = self._get_selected_entries()
        if not entries:
            QMessageBox.warning(self, "提示", "请先选择要导出的语料！\n\n提示：按住Ctrl或Shift可多选")
            return

        tab = self._get_current_tab()
        if not tab:
            return

        show_numbering = tab.data_show_numbering.isChecked()
        include_chinese = tab.data_include_chinese.isChecked()

        formatted_text = TextFormatter.format_entries(
            entries,
            show_numbering,
            include_chinese=include_chinese
        )

        self._show_text_export_dialog(formatted_text, len(entries))

    def quick_export_word(self):
        """快速导出选中语料到Word"""
        entries = self._get_selected_entries()
        if not entries:
            QMessageBox.warning(self, "提示", "请先选择要导出的语料！\n\n提示：按住Ctrl或Shift可多选")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存Word文档", "", "Word Documents (*.docx)"
        )

        if not file_path:
            return

        tab = self._get_current_tab()
        if not tab:
            return

        show_numbering = tab.data_show_numbering.isChecked()
        include_chinese = tab.data_include_chinese.isChecked()

        try:
            success = self.exporter.export(
                entries, file_path,
                table_width=5.0,
                font_size=10,
                line_spacing=1.15,
                show_numbering=show_numbering,
                entries_per_page=10,
                include_chinese=include_chinese,
                font_config=self.font_config
            )

            if success:
                QMessageBox.information(
                    self, "导出成功",
                    f"成功导出 {len(entries)} 条语料到:\n{file_path}"
                )
                self.statusBar().showMessage(f"导出成功: {len(entries)} 条", 3000)
            else:
                QMessageBox.critical(self, "导出失败", "导出过程中发生错误！")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"错误: {str(e)}")

    def quick_export_all_text(self):
        """快速导出当前Tab的所有语料为文本"""
        entry_type = self.get_current_entry_type()
        entries = self.db.get_entries_by_type(entry_type)

        if not entries:
            tab = self._get_current_tab()
            type_label = tab.type_label if tab else "语料"
            QMessageBox.warning(self, "提示", f"当前{type_label}Tab没有可导出的语料！")
            return

        tab = self._get_current_tab()
        if not tab:
            return

        show_numbering = tab.data_show_numbering.isChecked()
        include_chinese = tab.data_include_chinese.isChecked()

        formatted_text = TextFormatter.format_entries(
            entries,
            show_numbering,
            include_chinese=include_chinese
        )

        self._show_text_export_dialog(formatted_text, len(entries), title_prefix="全部")

    def quick_export_all_word(self):
        """快速导出当前Tab的所有语料到Word"""
        entry_type = self.get_current_entry_type()
        entries = self.db.get_entries_by_type(entry_type)

        if not entries:
            tab = self._get_current_tab()
            type_label = tab.type_label if tab else "语料"
            QMessageBox.warning(self, "提示", f"当前{type_label}Tab没有可导出的语料！")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存Word文档", "", "Word Documents (*.docx)"
        )

        if not file_path:
            return

        tab = self._get_current_tab()
        if not tab:
            return

        show_numbering = tab.data_show_numbering.isChecked()
        include_chinese = tab.data_include_chinese.isChecked()

        try:
            success = self.exporter.export(
                entries, file_path,
                table_width=5.0,
                font_size=10,
                line_spacing=1.15,
                show_numbering=show_numbering,
                entries_per_page=10,
                include_chinese=include_chinese,
                font_config=self.font_config
            )

            if success:
                QMessageBox.information(
                    self, "导出成功",
                    f"成功导出 {len(entries)} 条语料到:\n{file_path}"
                )
                self.statusBar().showMessage(f"导出成功: {len(entries)} 条", 3000)
            else:
                QMessageBox.critical(self, "导出失败", "导出过程中发生错误！")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"错误: {str(e)}")

    def _show_text_export_dialog(self, formatted_text, count, title_prefix=""):
        """显示文本导出对话框（消除重复代码）"""
        prefix = f"{title_prefix} " if title_prefix else ""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"导出文本 ({prefix}{count} 条)")
        dialog.setMinimumSize(800, 600)

        layout = QVBoxLayout()
        dialog.setLayout(layout)

        text_edit = QTextEdit()
        text_edit.setPlainText(formatted_text)
        text_edit.setReadOnly(True)
        text_edit.setFont(_get_monospace_font(11))
        layout.addWidget(text_edit)

        button_layout = QHBoxLayout()
        copy_btn = QPushButton("复制到剪贴板")
        copy_btn.clicked.connect(lambda: self._copy_to_clipboard(formatted_text, dialog))
        button_layout.addWidget(copy_btn)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        dialog.exec()

    def _copy_to_clipboard(self, text, dialog=None):
        """复制文本到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "复制成功", "文本已复制到剪贴板！")
        if dialog:
            dialog.close()

    def export_selected_to_text(self, data_table, selected_rows):
        """导出选中的语料为文本"""
        from gui import COL_ID
        if not selected_rows:
            return

        try:
            entries = []
            for index in selected_rows:
                row = index.row()
                entry_id = int(data_table.item(row, COL_ID).text())
                entry = self.db.get_entry(entry_id)
                if entry:
                    entries.append(entry)

            if not entries:
                QMessageBox.warning(self, "提示", "没有可导出的语料！")
                return

            tab = self._get_current_tab()
            if not tab:
                return

            show_numbering = tab.data_show_numbering.isChecked()
            include_chinese = tab.data_include_chinese.isChecked()

            formatted_text = TextFormatter.format_entries(
                entries,
                show_numbering,
                include_chinese=include_chinese
            )

            self._show_text_export_dialog(formatted_text, len(entries))

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def export_selected_to_word(self, data_table, selected_rows):
        """导出选中的语料到Word"""
        from gui import COL_ID
        if not selected_rows:
            return

        try:
            entries = []
            for index in selected_rows:
                row = index.row()
                entry_id = int(data_table.item(row, COL_ID).text())
                entry = self.db.get_entry(entry_id)
                if entry:
                    entries.append(entry)

            if not entries:
                QMessageBox.warning(self, "提示", "没有可导出的语料！")
                return

            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存Word文档", "", "Word Documents (*.docx)"
            )

            if not file_path:
                return

            tab = self._get_current_tab()
            if not tab:
                return

            show_numbering = tab.data_show_numbering.isChecked()
            include_chinese = tab.data_include_chinese.isChecked()

            success = self.exporter.export(
                entries, file_path,
                table_width=5.0,
                font_size=10,
                line_spacing=1.15,
                show_numbering=show_numbering,
                entries_per_page=10,
                include_chinese=include_chinese,
                font_config=self.font_config
            )

            if success:
                QMessageBox.information(
                    self,
                    "导出成功",
                    f"成功导出 {len(entries)} 条语料到:\n{file_path}"
                )
                self.statusBar().showMessage(f"导出成功: {len(entries)} 条", 3000)
            else:
                QMessageBox.critical(self, "导出失败", "导出过程中发生错误！")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def export_to_csv(self):
        """导出全部语料为CSV"""
        entries = self._get_export_entries()
        if not entries:
            QMessageBox.warning(self, "提示", "没有可导出的语料！")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出CSV", "", "CSV Files (*.csv)"
        )
        if not file_path:
            return

        self._write_csv(entries, file_path)

    def export_to_json(self):
        """导出全部语料为JSON"""
        entries = self._get_export_entries()
        if not entries:
            QMessageBox.warning(self, "提示", "没有可导出的语料！")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出JSON", "", "JSON Files (*.json)"
        )
        if not file_path:
            return

        self._write_json(entries, file_path)

    def _write_csv(self, entries, file_path):
        """将条目列表写入CSV文件"""
        try:
            fields = [
                'id', 'example_id', 'source_text', 'source_text_cn',
                'gloss', 'gloss_cn', 'translation', 'translation_cn',
                'notes', 'entry_type', 'group_id', 'group_name',
                'speaker', 'turn_number', 'created_at', 'updated_at', 'tags'
            ]
            with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
                writer.writeheader()
                for entry in entries:
                    writer.writerow(entry)
            QMessageBox.information(
                self, "导出成功",
                f"成功导出 {len(entries)} 条语料到:\n{file_path}"
            )
            self.statusBar().showMessage(f"CSV导出成功: {len(entries)} 条", 3000)
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"错误: {str(e)}")

    def _write_json(self, entries, file_path):
        """将条目列表写入JSON文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(entries, f, ensure_ascii=False, indent=2)
            QMessageBox.information(
                self, "导出成功",
                f"成功导出 {len(entries)} 条语料到:\n{file_path}"
            )
            self.statusBar().showMessage(f"JSON导出成功: {len(entries)} 条", 3000)
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"错误: {str(e)}")
