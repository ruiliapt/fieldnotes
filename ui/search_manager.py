"""搜索管理混入 - SearchManagerMixin"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox,
    QFileDialog, QComboBox, QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush

from ui.widgets import TagSelectorWidget


class SearchManagerMixin:
    """Mixin for search-related operations."""

    def create_search_tab(self):
        """创建检索标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # 搜索区域
        search_group = QGroupBox("检索条件")
        search_layout = QHBoxLayout()
        search_group.setLayout(search_layout)

        # 类型筛选
        search_layout.addWidget(QLabel("数据类型:"))
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(
            ["全部类型", "单词", "单句", "语篇", "对话"]
        )
        search_layout.addWidget(self.search_type_combo)

        search_layout.addWidget(QLabel("搜索字段:"))
        self.search_field_combo = QComboBox()
        self.search_field_combo.addItems(
            ["全部字段", "例句编号", "原文", "词汇分解", "翻译", "备注"]
        )
        search_layout.addWidget(self.search_field_combo)

        search_layout.addWidget(QLabel("关键词:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索关键词")
        search_layout.addWidget(self.search_input)

        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self.search_entries)
        search_layout.addWidget(search_btn)

        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self.reset_search)
        search_layout.addWidget(reset_btn)

        layout.addWidget(search_group)

        # 标签筛选区域
        tag_filter_group = QGroupBox("标签筛选")
        tag_filter_layout = QHBoxLayout()
        tag_filter_group.setLayout(tag_filter_layout)

        self.search_tag_checkboxes: dict[str, QCheckBox] = {}
        for category, tags in TagSelectorWidget.PREDEFINED_TAGS.items():
            for tag in tags:
                cb = QCheckBox(tag)
                self.search_tag_checkboxes[tag] = cb
                tag_filter_layout.addWidget(cb)

        tag_filter_layout.addStretch()
        layout.addWidget(tag_filter_group)

        # 搜索结果表格
        self.search_table = QTableWidget()
        self.search_table.setColumnCount(11)
        self.search_table.setHorizontalHeaderLabels(
            ["ID", "例句编号", "原文", "原文(汉字)", "词汇分解",
             "词汇分解(汉字)", "翻译", "翻译(汉字)", "备注", "创建时间", "标签"]
        )
        self.search_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.search_table.setAlternatingRowColors(True)
        layout.addWidget(self.search_table)

        # 搜索结果统计
        self.search_stats_label = QLabel("搜索结果: 0 条")
        layout.addWidget(self.search_stats_label)

        # 搜索结果导出按钮
        search_export_layout = QHBoxLayout()
        search_export_csv_btn = QPushButton("导出搜索结果 (CSV)")
        search_export_csv_btn.clicked.connect(self.export_search_results_csv)
        search_export_layout.addWidget(search_export_csv_btn)

        search_export_json_btn = QPushButton("导出搜索结果 (JSON)")
        search_export_json_btn.clicked.connect(self.export_search_results_json)
        search_export_layout.addWidget(search_export_json_btn)

        search_export_word_btn = QPushButton("导出搜索结果 (Word)")
        search_export_word_btn.clicked.connect(self.export_search_results_word)
        search_export_layout.addWidget(search_export_word_btn)

        search_export_layout.addStretch()
        layout.addLayout(search_export_layout)

        return widget

    def search_entries(self):
        """搜索语料"""
        from gui import (COL_ID, COL_EXAMPLE_ID, COL_SOURCE_TEXT, COL_SOURCE_TEXT_CN,
                         COL_GLOSS, COL_GLOSS_CN, COL_TRANSLATION, COL_TRANSLATION_CN,
                         COL_NOTES, COL_CREATED_AT, COL_TAGS)

        keyword = self.search_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "提示", "请输入搜索关键词！")
            return

        field_map = {
            "全部字段": "all",
            "例句编号": "example_id",
            "原文": "source_text",
            "词汇分解": "gloss",
            "翻译": "translation",
            "备注": "notes"
        }

        type_map = {
            "全部类型": None,
            "单词": "word",
            "单句": "sentence",
            "语篇": "discourse",
            "对话": "dialogue"
        }

        field = field_map[self.search_field_combo.currentText()]
        entry_type = type_map[self.search_type_combo.currentText()]

        # 收集选中的标签
        selected_tags = [tag for tag, cb in self.search_tag_checkboxes.items() if cb.isChecked()]

        results = self.db.search_entries(
            field, keyword, entry_type=entry_type,
            tags=selected_tags if selected_tags else None
        )

        self.search_table.setRowCount(len(results))

        for row, entry in enumerate(results):
            self.search_table.setItem(row, COL_ID, QTableWidgetItem(str(entry['id'])))
            self.search_table.setItem(row, COL_EXAMPLE_ID, QTableWidgetItem(entry['example_id'] or ""))
            self.search_table.setItem(row, COL_SOURCE_TEXT, QTableWidgetItem(entry['source_text'] or ""))
            self.search_table.setItem(row, COL_SOURCE_TEXT_CN, QTableWidgetItem(entry.get('source_text_cn', "") or ""))
            self.search_table.setItem(row, COL_GLOSS, QTableWidgetItem(entry['gloss'] or ""))
            self.search_table.setItem(row, COL_GLOSS_CN, QTableWidgetItem(entry.get('gloss_cn', "") or ""))
            self.search_table.setItem(row, COL_TRANSLATION, QTableWidgetItem(entry['translation'] or ""))
            self.search_table.setItem(row, COL_TRANSLATION_CN, QTableWidgetItem(entry.get('translation_cn', "") or ""))
            self.search_table.setItem(row, COL_NOTES, QTableWidgetItem(entry['notes'] or ""))

            # 创建时间
            created_at = entry.get('created_at', '') or ''
            if created_at and 'T' in created_at:
                created_at = created_at[:16].replace('T', ' ')
            item = QTableWidgetItem(created_at)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.search_table.setItem(row, COL_CREATED_AT, item)

            # 标签
            tags = entry.get('tags', '') or ''
            self.search_table.setItem(row, COL_TAGS, QTableWidgetItem(tags))

        # 搜索结果高亮
        highlight = self.theme_manager.get_highlight_color()
        for row in range(self.search_table.rowCount()):
            for col in range(self.search_table.columnCount()):
                item = self.search_table.item(row, col)
                if item and keyword.lower() in item.text().lower():
                    item.setBackground(QBrush(highlight))

        self.search_table.resizeColumnsToContents()
        self.search_stats_label.setText(f"搜索结果: {len(results)} 条")
        self.statusBar().showMessage(f"找到 {len(results)} 条匹配结果", 3000)

    def reset_search(self):
        """重置搜索"""
        self.search_input.clear()
        self.search_type_combo.setCurrentIndex(0)
        self.search_field_combo.setCurrentIndex(0)
        self.search_table.setRowCount(0)
        self.search_stats_label.setText("搜索结果: 0 条")
        # 清空标签筛选
        for cb in self.search_tag_checkboxes.values():
            cb.setChecked(False)

    def _get_search_result_entries(self) -> list:
        """获取搜索结果中的所有条目"""
        from gui import COL_ID
        entries = []
        for row in range(self.search_table.rowCount()):
            item = self.search_table.item(row, COL_ID)
            if item:
                entry_id = int(item.text())
                entry = self.db.get_entry(entry_id)
                if entry:
                    entries.append(entry)
        return entries

    def export_search_results_csv(self):
        """导出搜索结果为CSV"""
        entries = self._get_search_result_entries()
        if not entries:
            QMessageBox.warning(self, "提示", "没有搜索结果可导出！请先搜索。")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出搜索结果CSV", "", "CSV Files (*.csv)"
        )
        if file_path:
            self._write_csv(entries, file_path)

    def export_search_results_json(self):
        """导出搜索结果为JSON"""
        entries = self._get_search_result_entries()
        if not entries:
            QMessageBox.warning(self, "提示", "没有搜索结果可导出！请先搜索。")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出搜索结果JSON", "", "JSON Files (*.json)"
        )
        if file_path:
            self._write_json(entries, file_path)

    def export_search_results_word(self):
        """导出搜索结果为Word"""
        entries = self._get_search_result_entries()
        if not entries:
            QMessageBox.warning(self, "提示", "没有搜索结果可导出！请先搜索。")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出搜索结果Word", "", "Word Documents (*.docx)"
        )
        if not file_path:
            return
        try:
            success = self.exporter.export(
                entries, file_path,
                table_width=5.0, font_size=10, line_spacing=1.15,
                show_numbering=True, entries_per_page=10,
                include_chinese=False, font_config=self.font_config
            )
            if success:
                QMessageBox.information(
                    self, "导出成功",
                    f"成功导出 {len(entries)} 条搜索结果到:\n{file_path}"
                )
            else:
                QMessageBox.critical(self, "导出失败", "导出过程中发生错误！")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"错误: {str(e)}")
