"""
图形界面模块 - 使用PyQt6实现
"""
import sys
import json
import csv
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QMessageBox, QFileDialog, QDialog, QFormLayout, QSpinBox,
    QDoubleSpinBox, QCheckBox, QComboBox, QTabWidget, QGroupBox, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QAction

from database import CorpusDatabase
from exporter import WordExporter, TextFormatter
import os


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.db = CorpusDatabase()
        self.exporter = WordExporter()
        self.current_entry_id = None
        
        self.init_ui()
        self.refresh_table()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("Fieldnotes Lite - 田野笔记管理工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 创建标签页
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # 数据管理标签页
        data_tab = self.create_data_tab()
        tab_widget.addTab(data_tab, "数据管理")
        
        # 检索标签页
        search_tab = self.create_search_tab()
        tab_widget.addTab(search_tab, "检索")
        
        # 导出标签页
        export_tab = self.create_export_tab()
        tab_widget.addTab(export_tab, "导出")
        
        # 状态栏
        self.update_status_bar()
    
    def create_data_tab(self):
        """创建数据管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # 输入区域
        input_group = QGroupBox("语料录入")
        input_layout = QFormLayout()
        input_group.setLayout(input_layout)
        
        self.example_id_input = QLineEdit()
        self.example_id_input.setPlaceholderText("例：CJ001")
        input_layout.addRow("例句编号:", self.example_id_input)
        
        self.source_text_input = QTextEdit()
        self.source_text_input.setMaximumHeight(60)
        self.source_text_input.setPlaceholderText("输入原文（支持IPA和Unicode字符）")
        input_layout.addRow("原文:", self.source_text_input)
        
        self.gloss_input = QTextEdit()
        self.gloss_input.setMaximumHeight(60)
        self.gloss_input.setPlaceholderText("输入词汇分解/注释")
        input_layout.addRow("词汇分解:", self.gloss_input)
        
        self.translation_input = QTextEdit()
        self.translation_input.setMaximumHeight(60)
        self.translation_input.setPlaceholderText("输入翻译")
        input_layout.addRow("翻译:", self.translation_input)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText("输入备注（可选）")
        input_layout.addRow("备注:", self.notes_input)
        
        # 汉字注释字段
        self.source_text_cn_input = QTextEdit()
        self.source_text_cn_input.setMaximumHeight(60)
        self.source_text_cn_input.setPlaceholderText("输入原文的汉字注释（可选）")
        input_layout.addRow("原文(汉字):", self.source_text_cn_input)
        
        self.gloss_cn_input = QTextEdit()
        self.gloss_cn_input.setMaximumHeight(60)
        self.gloss_cn_input.setPlaceholderText("输入词汇分解的汉字注释（可选）")
        input_layout.addRow("词汇分解(汉字):", self.gloss_cn_input)
        
        self.translation_cn_input = QTextEdit()
        self.translation_cn_input.setMaximumHeight(60)
        self.translation_cn_input.setPlaceholderText("输入翻译的汉字版本（可选）")
        input_layout.addRow("翻译(汉字):", self.translation_cn_input)
        
        layout.addWidget(input_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("添加语料")
        add_btn.clicked.connect(self.add_entry)
        button_layout.addWidget(add_btn)
        
        update_btn = QPushButton("更新语料")
        update_btn.clicked.connect(self.update_entry)
        button_layout.addWidget(update_btn)
        
        delete_btn = QPushButton("删除语料")
        delete_btn.clicked.connect(self.delete_entry)
        button_layout.addWidget(delete_btn)
        
        clear_btn = QPushButton("清空输入")
        clear_btn.clicked.connect(self.clear_inputs)
        button_layout.addWidget(clear_btn)
        
        import_btn = QPushButton("批量导入")
        import_btn.clicked.connect(self.import_data)
        button_layout.addWidget(import_btn)
        
        layout.addLayout(button_layout)
        
        # 数据表格
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(6)
        self.data_table.setHorizontalHeaderLabels(
            ["ID", "例句编号", "原文", "词汇分解", "翻译", "备注"]
        )
        self.data_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.data_table.cellClicked.connect(self.load_entry_to_form)
        layout.addWidget(self.data_table)
        
        # 统计信息
        self.stats_label = QLabel("总计: 0 条语料")
        layout.addWidget(self.stats_label)
        
        return widget
    
    def create_search_tab(self):
        """创建检索标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # 搜索区域
        search_group = QGroupBox("检索条件")
        search_layout = QHBoxLayout()
        search_group.setLayout(search_layout)
        
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
        
        # 搜索结果表格
        self.search_table = QTableWidget()
        self.search_table.setColumnCount(6)
        self.search_table.setHorizontalHeaderLabels(
            ["ID", "例句编号", "原文", "词汇分解", "翻译", "备注"]
        )
        self.search_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.search_table)
        
        # 搜索结果统计
        self.search_stats_label = QLabel("搜索结果: 0 条")
        layout.addWidget(self.search_stats_label)
        
        return widget
    
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
        
        # 生成格式化文本按钮
        text_export_btn = QPushButton("生成对齐文本（可复制到Word）")
        text_export_btn.clicked.connect(self.generate_formatted_text)
        text_export_btn.setStyleSheet("QPushButton { padding: 10px; font-size: 14px; background-color: #4CAF50; color: white; }")
        button_layout.addWidget(text_export_btn)
        
        # Word导出按钮
        word_export_btn = QPushButton("导出到Word文档")
        word_export_btn.clicked.connect(self.export_to_word)
        word_export_btn.setStyleSheet("QPushButton { padding: 10px; font-size: 14px; }")
        button_layout.addWidget(word_export_btn)
        
        layout.addLayout(button_layout)
        
        # 格式化文本显示区域
        text_display_group = QGroupBox("格式化文本（可直接复制）")
        text_display_layout = QVBoxLayout()
        text_display_group.setLayout(text_display_layout)
        
        self.formatted_text_display = QTextEdit()
        self.formatted_text_display.setReadOnly(True)
        self.formatted_text_display.setMinimumHeight(400)
        # 使用等宽字体以保证对齐 - 尝试多个字体
        for font_name in ["Consolas", "Monaco", "Menlo", "DejaVu Sans Mono", "Courier New", "monospace"]:
            font = QFont(font_name, 11)
            font.setStyleHint(QFont.StyleHint.Monospace)
            font.setFixedPitch(True)
            self.formatted_text_display.setFont(font)
            # 测试字体是否可用
            if QFont(font_name).exactMatch():
                break
        text_display_layout.addWidget(self.formatted_text_display)
        
        # 复制按钮
        copy_btn = QPushButton("复制到剪贴板")
        copy_btn.clicked.connect(self.copy_formatted_text)
        text_display_layout.addWidget(copy_btn)
        
        layout.addWidget(text_display_group)
        
        return widget
    
    def add_entry(self):
        """添加语料"""
        example_id = self.example_id_input.text().strip()
        source_text = self.source_text_input.toPlainText().strip()
        gloss = self.gloss_input.toPlainText().strip()
        translation = self.translation_input.toPlainText().strip()
        notes = self.notes_input.toPlainText().strip()
        source_text_cn = self.source_text_cn_input.toPlainText().strip()
        gloss_cn = self.gloss_cn_input.toPlainText().strip()
        translation_cn = self.translation_cn_input.toPlainText().strip()
        
        if not source_text or not translation:
            QMessageBox.warning(self, "输入错误", "原文和翻译不能为空！")
            return
        
        try:
            self.db.insert_entry(example_id, source_text, gloss, translation, notes,
                               source_text_cn, gloss_cn, translation_cn)
            QMessageBox.information(self, "成功", "语料添加成功！")
            self.clear_inputs()
            self.refresh_table()
            self.statusBar().showMessage("添加成功", 3000)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加失败: {str(e)}")
    
    def update_entry(self):
        """更新语料"""
        if self.current_entry_id is None:
            QMessageBox.warning(self, "提示", "请先从表格中选择要更新的语料！")
            return
        
        example_id = self.example_id_input.text().strip()
        source_text = self.source_text_input.toPlainText().strip()
        gloss = self.gloss_input.toPlainText().strip()
        translation = self.translation_input.toPlainText().strip()
        notes = self.notes_input.toPlainText().strip()
        source_text_cn = self.source_text_cn_input.toPlainText().strip()
        gloss_cn = self.gloss_cn_input.toPlainText().strip()
        translation_cn = self.translation_cn_input.toPlainText().strip()
        
        if not source_text or not translation:
            QMessageBox.warning(self, "输入错误", "原文和翻译不能为空！")
            return
        
        try:
            self.db.update_entry(
                self.current_entry_id, example_id, source_text, gloss, translation, notes,
                source_text_cn, gloss_cn, translation_cn
            )
            QMessageBox.information(self, "成功", "语料更新成功！")
            self.clear_inputs()
            self.refresh_table()
            self.statusBar().showMessage("更新成功", 3000)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新失败: {str(e)}")
    
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
        self.example_id_input.clear()
        self.source_text_input.clear()
        self.gloss_input.clear()
        self.translation_input.clear()
        self.notes_input.clear()
        self.source_text_cn_input.clear()
        self.gloss_cn_input.clear()
        self.translation_cn_input.clear()
        self.current_entry_id = None
    
    def load_entry_to_form(self, row, column):
        """从表格加载语料到输入表单"""
        entry_id = int(self.data_table.item(row, 0).text())
        entry = self.db.get_entry(entry_id)
        
        if entry:
            self.current_entry_id = entry_id
            self.example_id_input.setText(entry['example_id'] or "")
            self.source_text_input.setPlainText(entry['source_text'] or "")
            self.gloss_input.setPlainText(entry['gloss'] or "")
            self.translation_input.setPlainText(entry['translation'] or "")
            self.notes_input.setPlainText(entry['notes'] or "")
            self.source_text_cn_input.setPlainText(entry.get('source_text_cn', "") or "")
            self.gloss_cn_input.setPlainText(entry.get('gloss_cn', "") or "")
            self.translation_cn_input.setPlainText(entry.get('translation_cn', "") or "")
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        # 新建数据库
        new_db_action = QAction("新建数据库...", self)
        new_db_action.setShortcut("Ctrl+N")
        new_db_action.triggered.connect(self.new_database)
        file_menu.addAction(new_db_action)
        
        # 打开数据库
        open_db_action = QAction("打开数据库...", self)
        open_db_action.setShortcut("Ctrl+O")
        open_db_action.triggered.connect(self.open_database)
        file_menu.addAction(open_db_action)
        
        # 另存为
        save_as_action = QAction("另存为...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_database_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # 退出
        quit_action = QAction("退出", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
    
    def update_status_bar(self):
        """更新状态栏显示当前数据库"""
        db_path = self.db.db_path
        # 显示简化路径
        if db_path.startswith(os.path.expanduser("~")):
            display_path = db_path.replace(os.path.expanduser("~"), "~")
        else:
            display_path = db_path
        self.statusBar().showMessage(f"数据库: {display_path}")
    
    def new_database(self):
        """创建新数据库"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "新建数据库",
            os.path.expanduser("~"),
            "数据库文件 (*.db);;所有文件 (*)"
        )
        
        if file_path:
            # 如果用户没有添加扩展名，自动添加
            if not file_path.endswith('.db'):
                file_path += '.db'
            
            try:
                # 关闭旧数据库
                self.db.close()
                # 创建新数据库
                self.db = CorpusDatabase(file_path)
                # 刷新界面
                self.refresh_table()
                self.update_status_bar()
                QMessageBox.information(
                    self,
                    "成功",
                    f"新数据库已创建：\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "错误",
                    f"创建数据库失败：\n{str(e)}"
                )
    
    def open_database(self):
        """打开现有数据库"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开数据库",
            os.path.expanduser("~"),
            "数据库文件 (*.db);;所有文件 (*)"
        )
        
        if file_path:
            try:
                # 关闭旧数据库
                self.db.close()
                # 打开新数据库
                self.db = CorpusDatabase(file_path)
                # 刷新界面
                self.refresh_table()
                self.update_status_bar()
                # 清空输入框
                self.clear_inputs()
                QMessageBox.information(
                    self,
                    "成功",
                    f"数据库已打开：\n{file_path}\n\n共有 {len(self.db.get_all_entries())} 条语料"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "错误",
                    f"打开数据库失败：\n{str(e)}"
                )
    
    def save_database_as(self):
        """数据库另存为"""
        # 获取当前数据库路径
        current_db = self.db.db_path
        current_dir = os.path.dirname(current_db)
        current_name = os.path.basename(current_db)
        
        # 建议的新文件名
        name_without_ext = os.path.splitext(current_name)[0]
        suggested_name = f"{name_without_ext}_副本.db"
        suggested_path = os.path.join(current_dir, suggested_name)
        
        # 选择保存位置
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "数据库另存为",
            suggested_path,
            "数据库文件 (*.db);;所有文件 (*)"
        )
        
        if file_path:
            # 如果用户没有添加扩展名，自动添加
            if not file_path.endswith('.db'):
                file_path += '.db'
            
            try:
                import shutil
                
                # 检查是否覆盖现有文件
                if os.path.exists(file_path):
                    reply = QMessageBox.question(
                        self,
                        "确认覆盖",
                        f"文件已存在：\n{file_path}\n\n是否覆盖？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply != QMessageBox.StandardButton.Yes:
                        return
                
                # 复制数据库文件
                shutil.copy2(current_db, file_path)
                
                # 询问是否切换到新数据库
                reply = QMessageBox.question(
                    self,
                    "另存为成功",
                    f"数据库已保存到：\n{file_path}\n\n是否切换到新数据库？\n"
                    f"(选择\"否\"将继续使用当前数据库)",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # 关闭旧数据库
                    self.db.close()
                    # 打开新数据库
                    self.db = CorpusDatabase(file_path)
                    # 刷新界面
                    self.refresh_table()
                    self.update_status_bar()
                    QMessageBox.information(
                        self,
                        "成功",
                        f"已切换到新数据库：\n{file_path}"
                    )
                else:
                    QMessageBox.information(
                        self,
                        "成功",
                        f"数据库已保存到：\n{file_path}\n\n当前仍在使用：\n{current_db}"
                    )
                    
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "错误",
                    f"另存为失败：\n{str(e)}"
                )
    
    def refresh_table(self):
        """刷新数据表格"""
        entries = self.db.get_all_entries()
        self.data_table.setRowCount(len(entries))
        
        for row, entry in enumerate(entries):
            self.data_table.setItem(row, 0, QTableWidgetItem(str(entry['id'])))
            self.data_table.setItem(row, 1, QTableWidgetItem(entry['example_id'] or ""))
            self.data_table.setItem(row, 2, QTableWidgetItem(entry['source_text'] or ""))
            self.data_table.setItem(row, 3, QTableWidgetItem(entry['gloss'] or ""))
            self.data_table.setItem(row, 4, QTableWidgetItem(entry['translation'] or ""))
            self.data_table.setItem(row, 5, QTableWidgetItem(entry['notes'] or ""))
        
        self.data_table.resizeColumnsToContents()
        self.stats_label.setText(f"总计: {len(entries)} 条语料")
    
    def search_entries(self):
        """搜索语料"""
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
        
        field = field_map[self.search_field_combo.currentText()]
        results = self.db.search_entries(field, keyword)
        
        self.search_table.setRowCount(len(results))
        
        for row, entry in enumerate(results):
            self.search_table.setItem(row, 0, QTableWidgetItem(str(entry['id'])))
            self.search_table.setItem(row, 1, QTableWidgetItem(entry['example_id'] or ""))
            self.search_table.setItem(row, 2, QTableWidgetItem(entry['source_text'] or ""))
            self.search_table.setItem(row, 3, QTableWidgetItem(entry['gloss'] or ""))
            self.search_table.setItem(row, 4, QTableWidgetItem(entry['translation'] or ""))
            self.search_table.setItem(row, 5, QTableWidgetItem(entry['notes'] or ""))
        
        self.search_table.resizeColumnsToContents()
        self.search_stats_label.setText(f"搜索结果: {len(results)} 条")
        self.statusBar().showMessage(f"找到 {len(results)} 条匹配结果", 3000)
    
    def reset_search(self):
        """重置搜索"""
        self.search_input.clear()
        self.search_table.setRowCount(0)
        self.search_stats_label.setText("搜索结果: 0 条")
    
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
            QMessageBox.information(self, "导入成功", f"成功导入 {count} 条语料！")
            self.refresh_table()
            self.statusBar().showMessage(f"导入成功: {count} 条", 3000)
            
        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"错误: {str(e)}")
    
    def generate_formatted_text(self):
        """生成格式化文本"""
        # 确定导出数据
        if self.export_selected_radio.isChecked() and self.search_table.rowCount() > 0:
            # 导出搜索结果
            entries = []
            for row in range(self.search_table.rowCount()):
                entry_id = int(self.search_table.item(row, 0).text())
                entry = self.db.get_entry(entry_id)
                if entry:
                    entries.append(entry)
        else:
            # 导出所有语料
            entries = self.db.get_all_entries()
        
        if not entries:
            QMessageBox.warning(self, "提示", "没有可导出的语料！")
            return
        
        # 获取格式参数
        show_numbering = self.show_numbering_checkbox.isChecked()
        include_chinese = self.include_chinese_checkbox.isChecked()
        
        # 生成格式化文本
        formatted_text = TextFormatter.format_entries(entries, show_numbering, 
                                                     include_chinese=include_chinese)
        
        # 显示在文本框中
        self.formatted_text_display.setPlainText(formatted_text)
        
        self.statusBar().showMessage(f"已生成 {len(entries)} 条语料的格式化文本", 3000)
        QMessageBox.information(
            self, "生成成功", 
            f"已生成 {len(entries)} 条语料的格式化文本！\n\n"
            "文本已按词对齐，可以直接复制到Word或其他文档。\n"
            "建议在Word中使用等宽字体（如Courier New）以保持对齐。"
        )
    
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
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存Word文档", "", "Word Documents (*.docx)"
        )
        
        if not file_path:
            return
        
        # 确定导出数据
        if self.export_selected_radio.isChecked() and self.search_table.rowCount() > 0:
            # 导出搜索结果
            entries = []
            for row in range(self.search_table.rowCount()):
                entry_id = int(self.search_table.item(row, 0).text())
                entry = self.db.get_entry(entry_id)
                if entry:
                    entries.append(entry)
        else:
            # 导出所有语料
            entries = self.db.get_all_entries()
        
        if not entries:
            QMessageBox.warning(self, "提示", "没有可导出的语料！")
            return
        
        # 获取导出参数
        show_numbering = self.show_numbering_checkbox.isChecked()
        include_chinese = self.include_chinese_checkbox.isChecked()
        
        # 执行导出
        try:
            success = self.exporter.export(
                entries, file_path,
                table_width=5.0,
                font_size=10,
                line_spacing=1.15,
                show_numbering=show_numbering,
                entries_per_page=10,
                include_chinese=include_chinese
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
    
    def closeEvent(self, event):
        """关闭事件处理"""
        self.db.close()
        event.accept()

