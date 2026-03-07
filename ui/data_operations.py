"""数据操作混入 - DataOperationsMixin"""
import json
import csv
import logging

from PyQt6.QtWidgets import (
    QMessageBox, QFileDialog, QMenu, QApplication, QDialog,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

logger = logging.getLogger(__name__)


class DataOperationsMixin:
    """Mixin for CRUD data operations on corpus entries."""

    # ---- CRUD ----

    def add_entry(self):
        """添加语料"""
        from gui import COL_ID
        tab = self._get_current_tab()
        if not tab:
            QMessageBox.warning(self, "错误", "无法获取当前Tab！")
            return

        example_id = tab.example_id_input.text().strip()
        source_text = tab.source_text_input.toPlainText().strip()
        gloss = tab.gloss_input.toPlainText().strip()
        translation = tab.translation_input.toPlainText().strip()
        notes = tab.notes_input.toPlainText().strip()
        source_text_cn = tab.source_text_cn_input.toPlainText().strip()
        gloss_cn = tab.gloss_cn_input.toPlainText().strip()
        translation_cn = tab.translation_cn_input.toPlainText().strip()
        tags = ','.join(tab.tag_selector.get_tags())

        if not source_text or not translation:
            QMessageBox.warning(self, "输入错误", "原文和翻译不能为空！")
            return

        entry_type = self.get_current_entry_type()

        # 验证
        warnings = self._validate_entry(tab)
        if warnings:
            tab.validation_label.setText('\n'.join(warnings))
            self._set_validation_style(tab.validation_label, True)
        else:
            tab.validation_label.setText("")
            self._set_validation_style(tab.validation_label, False)

        # 对于语篇和对话，检查是否选择了分组
        group_id = ""
        group_name = ""
        if entry_type in ["discourse", "dialogue"]:
            group_id, group_name = self.get_selected_group_info(entry_type)
            if not group_id:
                type_label = "语篇" if entry_type == "discourse" else "对话"
                QMessageBox.warning(
                    self,
                    "输入错误",
                    f"请先选择或创建{type_label}！\n\n点击'新建'按钮可以创建新的{type_label}。"
                )
                return

        try:
            self.db.insert_entry(
                example_id, source_text, gloss, translation, notes,
                source_text_cn, gloss_cn, translation_cn,
                entry_type=entry_type,
                group_id=group_id,
                group_name=group_name,
                tags=tags
            )
            QMessageBox.information(self, "成功", "语料添加成功！")
            self.clear_inputs()
            self.refresh_table()
            if entry_type in ["discourse", "dialogue"]:
                self.refresh_group_list(entry_type)
            self.statusBar().showMessage("添加成功", 3000)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加失败: {str(e)}")

    def update_entry(self):
        """更新语料"""
        if self.current_entry_id is None:
            QMessageBox.warning(self, "提示", "请先从表格中选择要更新的语料！")
            return

        tab = self._get_current_tab()
        if not tab:
            QMessageBox.warning(self, "错误", "无法获取当前Tab！")
            return

        example_id = tab.example_id_input.text().strip()
        source_text = tab.source_text_input.toPlainText().strip()
        gloss = tab.gloss_input.toPlainText().strip()
        translation = tab.translation_input.toPlainText().strip()
        notes = tab.notes_input.toPlainText().strip()
        source_text_cn = tab.source_text_cn_input.toPlainText().strip()
        gloss_cn = tab.gloss_cn_input.toPlainText().strip()
        translation_cn = tab.translation_cn_input.toPlainText().strip()
        tags = ','.join(tab.tag_selector.get_tags())

        if not source_text or not translation:
            QMessageBox.warning(self, "输入错误", "原文和翻译不能为空！")
            return

        entry_type = self.get_current_entry_type()

        # 验证
        warnings = self._validate_entry(tab, current_id=self.current_entry_id)
        if warnings:
            tab.validation_label.setText('\n'.join(warnings))
            self._set_validation_style(tab.validation_label, True)
        else:
            tab.validation_label.setText("")
            self._set_validation_style(tab.validation_label, False)

        # 对于语篇和对话，检查是否选择了分组
        group_id = ""
        group_name = ""
        if entry_type in ["discourse", "dialogue"]:
            group_id, group_name = self.get_selected_group_info(entry_type)
            if not group_id:
                type_label = "语篇" if entry_type == "discourse" else "对话"
                QMessageBox.warning(
                    self,
                    "输入错误",
                    f"请先选择或创建{type_label}！\n\n点击'新建'按钮可以创建新的{type_label}。"
                )
                return

        try:
            self.db.update_entry(
                self.current_entry_id, example_id, source_text, gloss, translation, notes,
                source_text_cn, gloss_cn, translation_cn,
                entry_type=entry_type,
                group_id=group_id,
                group_name=group_name,
                tags=tags
            )
            QMessageBox.information(self, "成功", "语料更新成功！")
            self.clear_inputs()
            self.refresh_table()
            if entry_type in ["discourse", "dialogue"]:
                self.refresh_group_list(entry_type)
            self.statusBar().showMessage("更新成功", 3000)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新失败: {str(e)}")

    def _validate_entry(self, tab, current_id: int = None) -> list:
        """验证输入，返回警告列表（不阻断保存）"""
        warnings = []
        src_words = tab.source_text_input.toPlainText().strip().split()
        gls_words = tab.gloss_input.toPlainText().strip().split()
        if src_words and gls_words and len(src_words) != len(gls_words):
            warnings.append(f"词数不匹配: 原文{len(src_words)}词, 词汇分解{len(gls_words)}词")
        eid = tab.example_id_input.text().strip()
        if eid and self.db.example_id_exists(eid, exclude_id=current_id):
            warnings.append(f"例句编号 '{eid}' 已存在")
        if not eid:
            warnings.append("建议填写例句编号")
        return warnings

    def delete_entry(self):
        """删除语料"""
        if self.current_entry_id is None:
            QMessageBox.warning(self, "提示", "请先从表格中选择要删除的语料！")
            return

        reply = QMessageBox.question(
            self, "确认删除", "确定要删除这条语料吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_entry(self.current_entry_id)
                QMessageBox.information(self, "成功", "语料删除成功！")
                self.clear_inputs()
                self.refresh_table()
                self.statusBar().showMessage("删除成功", 3000)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")

    def clear_inputs(self):
        """清空输入框"""
        tab = self._get_current_tab()
        if not tab:
            return

        tab.example_id_input.clear()
        tab.source_text_input.clear()
        tab.source_text_cn_input.clear()
        tab.gloss_input.clear()
        tab.gloss_cn_input.clear()
        tab.translation_input.clear()
        tab.translation_cn_input.clear()
        tab.notes_input.clear()
        tab.tag_selector.clear()
        tab.validation_label.setText("")
        self._set_validation_style(tab.validation_label, False)

        self.current_entry_id = None

    def load_entry_to_form(self, row, column):
        """从表格加载语料到输入表单"""
        from gui import COL_ID
        tab = self._get_current_tab()
        if not tab:
            return

        data_table = tab.data_table
        if not data_table:
            return

        entry_id = int(data_table.item(row, COL_ID).text())
        entry = self.db.get_entry(entry_id)

        if entry:
            self.current_entry_id = entry_id
            tab.example_id_input.setText(entry['example_id'] or "")
            tab.source_text_input.setPlainText(entry['source_text'] or "")
            tab.gloss_input.setPlainText(entry['gloss'] or "")
            tab.translation_input.setPlainText(entry['translation'] or "")
            tab.notes_input.setPlainText(entry['notes'] or "")
            tab.source_text_cn_input.setPlainText(entry.get('source_text_cn', "") or "")
            tab.gloss_cn_input.setPlainText(entry.get('gloss_cn', "") or "")
            tab.translation_cn_input.setPlainText(entry.get('translation_cn', "") or "")

            # 加载标签
            tags_str = entry.get('tags', '') or ''
            tags_list = [t.strip() for t in tags_str.split(',') if t.strip()]
            tab.tag_selector.set_tags(tags_list)

    def refresh_table(self):
        """刷新数据表格（根据当前Tab显示对应类型的数据）"""
        from gui import (COL_ID, COL_EXAMPLE_ID, COL_SOURCE_TEXT, COL_SOURCE_TEXT_CN,
                         COL_GLOSS, COL_GLOSS_CN, COL_TRANSLATION, COL_TRANSLATION_CN,
                         COL_NOTES, COL_CREATED_AT, COL_TAGS)
        from PyQt6.QtWidgets import QTableWidgetItem

        tab = self._get_current_tab()
        if not tab:
            return

        data_table = tab.data_table
        stats_label = tab.stats_label

        entry_type = self.get_current_entry_type()
        entries = self.db.get_entries_by_type(entry_type)
        data_table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            data_table.setItem(row, COL_ID, QTableWidgetItem(str(entry['id'])))
            data_table.setItem(row, COL_EXAMPLE_ID, QTableWidgetItem(entry['example_id'] or ""))
            data_table.setItem(row, COL_SOURCE_TEXT, QTableWidgetItem(entry['source_text'] or ""))
            data_table.setItem(row, COL_SOURCE_TEXT_CN, QTableWidgetItem(entry.get('source_text_cn', "") or ""))
            data_table.setItem(row, COL_GLOSS, QTableWidgetItem(entry['gloss'] or ""))
            data_table.setItem(row, COL_GLOSS_CN, QTableWidgetItem(entry.get('gloss_cn', "") or ""))
            data_table.setItem(row, COL_TRANSLATION, QTableWidgetItem(entry['translation'] or ""))
            data_table.setItem(row, COL_TRANSLATION_CN, QTableWidgetItem(entry.get('translation_cn', "") or ""))
            data_table.setItem(row, COL_NOTES, QTableWidgetItem(entry['notes'] or ""))

            # 创建时间
            created_at = entry.get('created_at', '') or ''
            if created_at and 'T' in created_at:
                created_at = created_at[:16].replace('T', ' ')
            item = QTableWidgetItem(created_at)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            data_table.setItem(row, COL_CREATED_AT, item)

            # 标签
            tags = entry.get('tags', '') or ''
            data_table.setItem(row, COL_TAGS, QTableWidgetItem(tags))

        data_table.resizeColumnsToContents()
        stats_label.setText(f"{tab.type_label}总计: {len(entries)} 条")

    def import_data(self):
        """批量导入数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择导入文件", "", "JSON Files (*.json);;CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            entries = []
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    entries = json.load(f)
            elif file_path.endswith('.csv'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    entries = list(reader)

            count = self.db.import_from_list(entries)
            logger.info("导入完成: %d 条, 来源: %s", count, file_path)
            QMessageBox.information(self, "导入成功", f"成功导入 {count} 条语料！")
            self.refresh_table()
            self.statusBar().showMessage(f"导入成功: {count} 条", 3000)

        except Exception as e:
            logger.error("导入失败: %s", e)
            QMessageBox.critical(self, "导入失败", f"错误: {str(e)}")

    # ---- Table context menu ----

    def show_table_context_menu(self, pos):
        """显示表格右键菜单"""
        from gui import COL_ID
        tab = self._get_current_tab()
        if not tab:
            return

        data_table = tab.data_table
        selected_rows = data_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        menu = QMenu(self)
        selected_count = len(selected_rows)

        edit_action = QAction("编辑 (加载到表单)", self)
        edit_action.triggered.connect(lambda: self.load_selected_entry_from_menu(data_table, selected_rows))
        menu.addAction(edit_action)

        menu.addSeparator()

        delete_action = QAction(f"删除选中项 ({selected_count} 条)", self)
        delete_action.triggered.connect(lambda: self.delete_selected_entries(data_table, selected_rows))
        menu.addAction(delete_action)

        menu.addSeparator()

        export_text_action = QAction(f"导出为文本 ({selected_count} 条)", self)
        export_text_action.triggered.connect(lambda: self.export_selected_to_text(data_table, selected_rows))
        menu.addAction(export_text_action)

        export_word_action = QAction(f"导出为Word ({selected_count} 条)", self)
        export_word_action.triggered.connect(lambda: self.export_selected_to_word(data_table, selected_rows))
        menu.addAction(export_word_action)

        menu.addSeparator()

        copy_action = QAction("复制单元格内容", self)
        copy_action.triggered.connect(lambda: self.copy_cell_content(data_table))
        menu.addAction(copy_action)

        if selected_count > 0:
            menu.addSeparator()

            batch_add_tag_action = QAction(f"批量添加标签 ({selected_count} 条)", self)
            batch_add_tag_action.triggered.connect(
                lambda: self.batch_tag_operation(data_table, selected_rows, 'add')
            )
            menu.addAction(batch_add_tag_action)

            batch_remove_tag_action = QAction(f"批量移除标签 ({selected_count} 条)", self)
            batch_remove_tag_action.triggered.connect(
                lambda: self.batch_tag_operation(data_table, selected_rows, 'remove')
            )
            menu.addAction(batch_remove_tag_action)

        menu.exec(data_table.viewport().mapToGlobal(pos))

    def load_selected_entry_from_menu(self, data_table, selected_rows):
        """从右键菜单加载选中的条目到表单"""
        if not selected_rows:
            return
        first_row = selected_rows[0].row()
        self.load_entry_to_form(first_row, 0)

    def delete_selected_entries(self, data_table, selected_rows):
        """删除选中的多条语料"""
        from gui import COL_ID
        if not selected_rows:
            return

        count = len(selected_rows)

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除选中的 {count} 条语料吗？\n\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                entry_ids = []
                for index in selected_rows:
                    row = index.row()
                    entry_id = int(data_table.item(row, COL_ID).text())
                    entry_ids.append(entry_id)

                deleted_count = 0
                for entry_id in entry_ids:
                    if self.db.delete_entry(entry_id):
                        deleted_count += 1

                QMessageBox.information(
                    self,
                    "删除成功",
                    f"成功删除 {deleted_count} 条语料！"
                )

                self.clear_inputs()
                self.refresh_table()
                self.statusBar().showMessage(f"删除成功: {deleted_count} 条", 3000)

            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")

    def copy_cell_content(self, data_table):
        """复制选中单元格的内容"""
        try:
            current_item = data_table.currentItem()
            if current_item:
                text = current_item.text()
                clipboard = QApplication.clipboard()
                clipboard.setText(text)
                self.statusBar().showMessage("已复制单元格内容", 2000)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"复制失败: {str(e)}")

    def batch_tag_operation(self, data_table, selected_rows, mode: str):
        """批量标签操作入口"""
        from gui import COL_ID, BatchTagDialog
        entry_ids = []
        for index in selected_rows:
            row = index.row()
            entry_ids.append(int(data_table.item(row, COL_ID).text()))

        dialog = BatchTagDialog(self, mode=mode)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tags = dialog.get_tags()
            if not tags:
                QMessageBox.warning(self, "提示", "请至少选择一个标签！")
                return

            if mode == 'add':
                count = self.db.batch_update_tags(entry_ids, add_tags=tags)
            else:
                count = self.db.batch_update_tags(entry_ids, remove_tags=tags)

            action = "添加" if mode == 'add' else "移除"
            QMessageBox.information(self, "成功", f"已为 {count} 条语料{action}标签！")
            self.refresh_table()
