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
    QDoubleSpinBox, QCheckBox, QComboBox, QTabWidget, QGroupBox, QApplication,
    QMenu
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QAction, QShortcut, QKeySequence

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
        
        # 加载字体配置
        self.font_config = self.load_font_config()
        
        self.init_ui()
        self.apply_fonts()  # 应用字体
        self.setup_global_shortcuts()  # 设置全局快捷键
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
        """创建数据管理标签页（包含4个子Tab）"""
        widget = QWidget()
        main_layout = QVBoxLayout()
        widget.setLayout(main_layout)
        
        # 创建子Tab容器
        self.data_sub_tabs = QTabWidget()
        main_layout.addWidget(self.data_sub_tabs)
        
        # 创建4个子Tab
        self.word_tab = self.create_word_tab()
        self.sentence_tab = self.create_sentence_tab()
        self.discourse_tab = self.create_discourse_tab()
        self.dialogue_tab = self.create_dialogue_tab()
        
        self.data_sub_tabs.addTab(self.word_tab, "单词")
        self.data_sub_tabs.addTab(self.sentence_tab, "单句")
        self.data_sub_tabs.addTab(self.discourse_tab, "语篇")
        self.data_sub_tabs.addTab(self.dialogue_tab, "对话")
        
        # 当Tab切换时刷新表格
        self.data_sub_tabs.currentChanged.connect(lambda: self.refresh_table())
        
        return widget
    
    def create_entry_type_tab(self, entry_type, type_label):
        """通用的条目类型Tab创建方法
        
        Args:
            entry_type: word/sentence/discourse/dialogue
            type_label: 显示标签（单词/单句/语篇/对话）
        """
        widget = QWidget()
        main_layout = QHBoxLayout()
        widget.setLayout(main_layout)
        
        # ===== 左侧：录入区域 =====
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        left_widget.setMaximumWidth(500)
        
        # 输入区域
        input_group = QGroupBox("语料录入")
        input_layout = QFormLayout()
        input_group.setLayout(input_layout)
        
        # 例句编号（为每个Tab创建独立的输入框）
        example_id_input = QLineEdit()
        example_id_input.setPlaceholderText("例：CJ001")
        input_layout.addRow("例句编号:", example_id_input)
        
        # 对于语篇和对话，添加分组选择
        if entry_type in ["discourse", "dialogue"]:
            group_label = "所属语篇:" if entry_type == "discourse" else "所属对话:"
            
            # 分组选择区域（包含下拉框和新建按钮）
            group_select_layout = QHBoxLayout()
            
            # 创建并存储分组选择下拉框（根据类型命名）
            group_combo = QComboBox()
            group_combo.setEditable(False)
            group_combo.setMinimumWidth(200)
            group_select_layout.addWidget(group_combo, 1)
            
            # 新建按钮
            new_group_btn = QPushButton("新建")
            new_group_btn.setMaximumWidth(60)
            new_group_btn.clicked.connect(
                lambda: self.create_new_group(entry_type)
            )
            group_select_layout.addWidget(new_group_btn)
            
            # 刷新按钮
            refresh_group_btn = QPushButton("刷新")
            refresh_group_btn.setMaximumWidth(60)
            refresh_group_btn.clicked.connect(
                lambda: self.refresh_group_list(entry_type)
            )
            group_select_layout.addWidget(refresh_group_btn)
            
            input_layout.addRow(group_label, group_select_layout)
            
            # 根据类型存储combo box的引用
            if entry_type == "discourse":
                self.discourse_group_combo = group_combo
                # 初始加载语篇列表
                self.refresh_group_list("discourse")
            else:  # dialogue
                self.dialogue_group_combo = group_combo
                # 初始加载对话列表
                self.refresh_group_list("dialogue")
        
        # 原文
        source_text_input = QTextEdit()
        source_text_input.setMaximumHeight(60)
        source_text_input.setPlaceholderText("输入原文（支持IPA和Unicode字符）")
        self.setup_text_edit_context_menu(source_text_input)
        input_layout.addRow("原文:", source_text_input)
        
        # 原文(汉字) - 紧跟原文
        source_text_cn_input = QTextEdit()
        source_text_cn_input.setMaximumHeight(60)
        source_text_cn_input.setPlaceholderText("输入原文的汉字注释（可选）")
        self.setup_text_edit_context_menu(source_text_cn_input)
        input_layout.addRow("原文(汉字):", source_text_cn_input)
        
        # 词汇分解
        gloss_input = QTextEdit()
        gloss_input.setMaximumHeight(60)
        gloss_input.setPlaceholderText("输入词汇分解/注释")
        self.setup_text_edit_context_menu(gloss_input)
        input_layout.addRow("词汇分解:", gloss_input)
        
        # 词汇分解(汉字) - 紧跟词汇分解
        gloss_cn_input = QTextEdit()
        gloss_cn_input.setMaximumHeight(60)
        gloss_cn_input.setPlaceholderText("输入词汇分解的汉字注释（可选）")
        self.setup_text_edit_context_menu(gloss_cn_input)
        input_layout.addRow("词汇分解(汉字):", gloss_cn_input)
        
        # 翻译
        translation_input = QTextEdit()
        translation_input.setMaximumHeight(60)
        translation_input.setPlaceholderText("输入翻译")
        self.setup_text_edit_context_menu(translation_input)
        input_layout.addRow("翻译:", translation_input)
        
        # 翻译(汉字) - 紧跟翻译
        translation_cn_input = QTextEdit()
        translation_cn_input.setMaximumHeight(60)
        translation_cn_input.setPlaceholderText("输入翻译的汉字版本（可选）")
        self.setup_text_edit_context_menu(translation_cn_input)
        input_layout.addRow("翻译(汉字):", translation_cn_input)
        
        # 备注
        notes_input = QTextEdit()
        notes_input.setMaximumHeight(60)
        notes_input.setPlaceholderText("输入备注（可选）")
        self.setup_text_edit_context_menu(notes_input)
        input_layout.addRow("备注:", notes_input)
        
        left_layout.addWidget(input_group)
        
        # 按钮区域
        button_group = QGroupBox("操作")
        button_group_layout = QVBoxLayout()
        button_group.setLayout(button_group_layout)
        
        add_btn = QPushButton("添加语料")
        add_btn.clicked.connect(self.add_entry)
        button_group_layout.addWidget(add_btn)
        
        update_btn = QPushButton("更新语料")
        update_btn.clicked.connect(self.update_entry)
        button_group_layout.addWidget(update_btn)
        
        delete_btn = QPushButton("删除语料")
        delete_btn.clicked.connect(self.delete_entry)
        button_group_layout.addWidget(delete_btn)
        
        clear_btn = QPushButton("清空输入")
        clear_btn.clicked.connect(self.clear_inputs)
        button_group_layout.addWidget(clear_btn)
        
        import_btn = QPushButton("批量导入")
        import_btn.clicked.connect(self.import_data)
        button_group_layout.addWidget(import_btn)
        
        left_layout.addWidget(button_group)
        left_layout.addStretch()  # 添加弹性空间
        
        # ===== 右侧：数据列表区域 =====
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        # 数据表格（每个Tab独立）
        list_group = QGroupBox("已录入语料")
        list_layout = QVBoxLayout()
        list_group.setLayout(list_layout)
        
        data_table = QTableWidget()
        data_table.setColumnCount(9)
        data_table.setHorizontalHeaderLabels(
            ["ID", "例句编号", "原文", "原文(汉字)", "词汇分解", "词汇分解(汉字)", "翻译", "翻译(汉字)", "备注"]
        )
        data_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        data_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)  # 支持多选
        data_table.cellClicked.connect(self.load_entry_to_form)
        # 设置右键菜单
        data_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        data_table.customContextMenuRequested.connect(self.show_table_context_menu)
        list_layout.addWidget(data_table)
        
        # 统计信息
        stats_label = QLabel("总计: 0 条语料")
        list_layout.addWidget(stats_label)
        
        right_layout.addWidget(list_group)
        
        # ===== 导出控制区域 =====
        export_group = QGroupBox("快速导出")
        export_layout = QVBoxLayout()
        export_group.setLayout(export_layout)
        
        # 导出选项（每个Tab独立）
        options_layout = QHBoxLayout()
        
        data_show_numbering = QCheckBox("显示编号")
        data_show_numbering.setChecked(True)
        options_layout.addWidget(data_show_numbering)
        
        data_include_chinese = QCheckBox("包含汉字")
        data_include_chinese.setChecked(False)
        options_layout.addWidget(data_include_chinese)
        
        options_layout.addStretch()
        export_layout.addLayout(options_layout)
        
        # 导出按钮
        export_buttons_layout = QHBoxLayout()
        
        export_text_btn = QPushButton("生成文本")
        export_text_btn.setToolTip("将选中的语料生成对齐文本")
        export_text_btn.clicked.connect(self.quick_export_text)
        export_buttons_layout.addWidget(export_text_btn)
        
        export_word_btn = QPushButton("导出Word")
        export_word_btn.setToolTip("将选中的语料导出到Word文档")
        export_word_btn.clicked.connect(self.quick_export_word)
        export_buttons_layout.addWidget(export_word_btn)
        
        export_all_text_btn = QPushButton("全部文本")
        export_all_text_btn.setToolTip("将所有语料生成对齐文本")
        export_all_text_btn.clicked.connect(self.quick_export_all_text)
        export_buttons_layout.addWidget(export_all_text_btn)
        
        export_all_word_btn = QPushButton("全部Word")
        export_all_word_btn.setToolTip("将所有语料导出到Word文档")
        export_all_word_btn.clicked.connect(self.quick_export_all_word)
        export_buttons_layout.addWidget(export_all_word_btn)
        
        export_layout.addLayout(export_buttons_layout)
        
        right_layout.addWidget(export_group)
        
        # 将左右两侧添加到主布局
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)
        
        # 存储当前Tab的类型信息和所有组件引用
        widget.setProperty("entry_type", entry_type)
        widget.setProperty("type_label", type_label)
        widget.setProperty("example_id_input", example_id_input)
        widget.setProperty("source_text_input", source_text_input)
        widget.setProperty("source_text_cn_input", source_text_cn_input)
        widget.setProperty("gloss_input", gloss_input)
        widget.setProperty("gloss_cn_input", gloss_cn_input)
        widget.setProperty("translation_input", translation_input)
        widget.setProperty("translation_cn_input", translation_cn_input)
        widget.setProperty("notes_input", notes_input)
        widget.setProperty("data_table", data_table)
        widget.setProperty("stats_label", stats_label)
        widget.setProperty("data_show_numbering", data_show_numbering)
        widget.setProperty("data_include_chinese", data_include_chinese)
        
        return widget
    
    def create_word_tab(self):
        """创建单词Tab"""
        return self.create_entry_type_tab("word", "单词")
    
    def create_sentence_tab(self):
        """创建单句Tab"""
        return self.create_entry_type_tab("sentence", "单句")
    
    def create_discourse_tab(self):
        """创建语篇Tab"""
        return self.create_entry_type_tab("discourse", "语篇")
    
    def create_dialogue_tab(self):
        """创建对话Tab"""
        return self.create_entry_type_tab("dialogue", "对话")
    
    def get_current_entry_type(self):
        """获取当前选中Tab的条目类型"""
        current_widget = self.data_sub_tabs.currentWidget()
        if current_widget:
            return current_widget.property("entry_type") or "sentence"
        return "sentence"
    
    def refresh_group_list(self, entry_type):
        """刷新语篇/对话列表
        
        Args:
            entry_type: discourse 或 dialogue
        """
        # 获取对应的combo box
        combo = None
        if entry_type == "discourse":
            combo = getattr(self, 'discourse_group_combo', None)
        elif entry_type == "dialogue":
            combo = getattr(self, 'dialogue_group_combo', None)
        
        if not combo:
            return
        
        # 清空并重新加载
        combo.clear()
        combo.addItem("--- 请选择 ---", "")
        
        # 从数据库获取分组列表
        groups = self.db.get_groups_by_type(entry_type)
        
        for group in groups:
            display_text = f"{group['group_id']} - {group['group_name']} ({group['count']}句)"
            combo.addItem(display_text, group['group_id'])
    
    def create_new_group(self, entry_type):
        """创建新的语篇/对话分组
        
        Args:
            entry_type: discourse 或 dialogue
        """
        from PyQt6.QtWidgets import QInputDialog
        
        type_label = "语篇" if entry_type == "discourse" else "对话"
        
        # 让用户输入分组名称
        group_name, ok = QInputDialog.getText(
            self,
            f"新建{type_label}",
            f"请输入{type_label}名称:",
            QLineEdit.EchoMode.Normal,
            ""
        )
        
        if ok and group_name.strip():
            group_name = group_name.strip()
            
            # 生成新的group_id
            group_id = self.db.get_next_group_id(entry_type)
            
            QMessageBox.information(
                self,
                "成功",
                f"已创建{type_label}: {group_id} - {group_name}\n\n"
                f"现在可以在下拉框中选择该{type_label}，然后录入句子。"
            )
            
            # 刷新列表并自动选中新创建的
            self.refresh_group_list(entry_type)
            
            # 在combo box中选中新创建的分组
            combo = None
            if entry_type == "discourse":
                combo = getattr(self, 'discourse_group_combo', None)
            elif entry_type == "dialogue":
                combo = getattr(self, 'dialogue_group_combo', None)
            
            if combo:
                # 查找并选中新创建的group_id
                for i in range(combo.count()):
                    if combo.itemData(i) == group_id:
                        combo.setCurrentIndex(i)
                        break
    
    def get_selected_group_info(self, entry_type):
        """获取当前选中的分组信息
        
        Args:
            entry_type: discourse 或 dialogue
            
        Returns:
            (group_id, group_name) 或 (None, None)
        """
        combo = None
        if entry_type == "discourse":
            combo = getattr(self, 'discourse_group_combo', None)
        elif entry_type == "dialogue":
            combo = getattr(self, 'dialogue_group_combo', None)
        
        if not combo or combo.currentIndex() <= 0:
            return None, None
        
        group_id = combo.currentData()
        if not group_id:
            return None, None
        
        # 从显示文本中提取group_name
        text = combo.currentText()
        # 格式: "DSC001 - 民间故事 (3句)"
        if " - " in text and " (" in text:
            group_name = text.split(" - ")[1].split(" (")[0]
        else:
            group_name = text
        
        return group_id, group_name
    
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
        
        # 搜索结果表格
        self.search_table = QTableWidget()
        self.search_table.setColumnCount(9)
        self.search_table.setHorizontalHeaderLabels(
            ["ID", "例句编号", "原文", "原文(汉字)", "词汇分解", "词汇分解(汉字)", "翻译", "翻译(汉字)", "备注"]
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
        # 从当前Tab获取输入框
        current_widget = self.data_sub_tabs.currentWidget()
        if not current_widget:
            QMessageBox.warning(self, "错误", "无法获取当前Tab！")
            return
        
        example_id_input = current_widget.property("example_id_input")
        source_text_input = current_widget.property("source_text_input")
        source_text_cn_input = current_widget.property("source_text_cn_input")
        gloss_input = current_widget.property("gloss_input")
        gloss_cn_input = current_widget.property("gloss_cn_input")
        translation_input = current_widget.property("translation_input")
        translation_cn_input = current_widget.property("translation_cn_input")
        notes_input = current_widget.property("notes_input")
        
        if not example_id_input or not source_text_input:
            QMessageBox.warning(self, "错误", "无法获取输入框！")
            return
        
        example_id = example_id_input.text().strip()
        source_text = source_text_input.toPlainText().strip()
        gloss = gloss_input.toPlainText().strip()
        translation = translation_input.toPlainText().strip()
        notes = notes_input.toPlainText().strip()
        source_text_cn = source_text_cn_input.toPlainText().strip()
        gloss_cn = gloss_cn_input.toPlainText().strip()
        translation_cn = translation_cn_input.toPlainText().strip()
        
        if not source_text or not translation:
            QMessageBox.warning(self, "输入错误", "原文和翻译不能为空！")
            return
        
        entry_type = self.get_current_entry_type()
        
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
                group_name=group_name
            )
            QMessageBox.information(self, "成功", "语料添加成功！")
            self.clear_inputs()
            self.refresh_table()
            # 刷新分组列表（更新计数）
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
        
        # 从当前Tab获取输入框
        current_widget = self.data_sub_tabs.currentWidget()
        if not current_widget:
            QMessageBox.warning(self, "错误", "无法获取当前Tab！")
            return
        
        example_id_input = current_widget.property("example_id_input")
        source_text_input = current_widget.property("source_text_input")
        source_text_cn_input = current_widget.property("source_text_cn_input")
        gloss_input = current_widget.property("gloss_input")
        gloss_cn_input = current_widget.property("gloss_cn_input")
        translation_input = current_widget.property("translation_input")
        translation_cn_input = current_widget.property("translation_cn_input")
        notes_input = current_widget.property("notes_input")
        
        if not example_id_input or not source_text_input:
            QMessageBox.warning(self, "错误", "无法获取输入框！")
            return
        
        example_id = example_id_input.text().strip()
        source_text = source_text_input.toPlainText().strip()
        gloss = gloss_input.toPlainText().strip()
        translation = translation_input.toPlainText().strip()
        notes = notes_input.toPlainText().strip()
        source_text_cn = source_text_cn_input.toPlainText().strip()
        gloss_cn = gloss_cn_input.toPlainText().strip()
        translation_cn = translation_cn_input.toPlainText().strip()
        
        if not source_text or not translation:
            QMessageBox.warning(self, "输入错误", "原文和翻译不能为空！")
            return
        
        entry_type = self.get_current_entry_type()
        
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
                group_name=group_name
            )
            QMessageBox.information(self, "成功", "语料更新成功！")
            self.clear_inputs()
            self.refresh_table()
            # 刷新分组列表（更新计数）
            if entry_type in ["discourse", "dialogue"]:
                self.refresh_group_list(entry_type)
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
        # 从当前Tab获取输入框
        current_widget = self.data_sub_tabs.currentWidget()
        if not current_widget:
            return
        
        example_id_input = current_widget.property("example_id_input")
        source_text_input = current_widget.property("source_text_input")
        source_text_cn_input = current_widget.property("source_text_cn_input")
        gloss_input = current_widget.property("gloss_input")
        gloss_cn_input = current_widget.property("gloss_cn_input")
        translation_input = current_widget.property("translation_input")
        translation_cn_input = current_widget.property("translation_cn_input")
        notes_input = current_widget.property("notes_input")
        
        if example_id_input:
            example_id_input.clear()
        if source_text_input:
            source_text_input.clear()
        if gloss_input:
            gloss_input.clear()
        if translation_input:
            translation_input.clear()
        if notes_input:
            notes_input.clear()
        if source_text_cn_input:
            source_text_cn_input.clear()
        if gloss_cn_input:
            gloss_cn_input.clear()
        if translation_cn_input:
            translation_cn_input.clear()
        
        self.current_entry_id = None
    
    def load_entry_to_form(self, row, column):
        """从表格加载语料到输入表单"""
        # 从当前Tab获取表格
        current_widget = self.data_sub_tabs.currentWidget()
        if not current_widget:
            return
        
        data_table = current_widget.property("data_table")
        if not data_table:
            return
        
        entry_id = int(data_table.item(row, 0).text())
        entry = self.db.get_entry(entry_id)
        
        if entry:
            
            example_id_input = current_widget.property("example_id_input")
            source_text_input = current_widget.property("source_text_input")
            source_text_cn_input = current_widget.property("source_text_cn_input")
            gloss_input = current_widget.property("gloss_input")
            gloss_cn_input = current_widget.property("gloss_cn_input")
            translation_input = current_widget.property("translation_input")
            translation_cn_input = current_widget.property("translation_cn_input")
            notes_input = current_widget.property("notes_input")
            
            if not example_id_input or not source_text_input:
                return
            
            self.current_entry_id = entry_id
            example_id_input.setText(entry['example_id'] or "")
            source_text_input.setPlainText(entry['source_text'] or "")
            gloss_input.setPlainText(entry['gloss'] or "")
            translation_input.setPlainText(entry['translation'] or "")
            notes_input.setPlainText(entry['notes'] or "")
            source_text_cn_input.setPlainText(entry.get('source_text_cn', "") or "")
            gloss_cn_input.setPlainText(entry.get('gloss_cn', "") or "")
            translation_cn_input.setPlainText(entry.get('translation_cn', "") or "")
    
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
        
        # 设置菜单
        settings_menu = menubar.addMenu("设置")
        
        # 字体设置
        font_settings_action = QAction("字体设置...", self)
        font_settings_action.triggered.connect(self.open_font_settings)
        settings_menu.addAction(font_settings_action)
    
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
        """刷新数据表格（根据当前Tab显示对应类型的数据）"""
        # 获取当前Tab的表格和标签
        current_widget = self.data_sub_tabs.currentWidget()
        if not current_widget:
            return
        
        data_table = current_widget.property("data_table")
        stats_label = current_widget.property("stats_label")
        
        if not data_table or not stats_label:
            return
        
        entry_type = self.get_current_entry_type()
        entries = self.db.get_entries_by_type(entry_type)
        data_table.setRowCount(len(entries))
        
        for row, entry in enumerate(entries):
            data_table.setItem(row, 0, QTableWidgetItem(str(entry['id'])))
            data_table.setItem(row, 1, QTableWidgetItem(entry['example_id'] or ""))
            data_table.setItem(row, 2, QTableWidgetItem(entry['source_text'] or ""))
            data_table.setItem(row, 3, QTableWidgetItem(entry.get('source_text_cn', "") or ""))
            data_table.setItem(row, 4, QTableWidgetItem(entry['gloss'] or ""))
            data_table.setItem(row, 5, QTableWidgetItem(entry.get('gloss_cn', "") or ""))
            data_table.setItem(row, 6, QTableWidgetItem(entry['translation'] or ""))
            data_table.setItem(row, 7, QTableWidgetItem(entry.get('translation_cn', "") or ""))
            data_table.setItem(row, 8, QTableWidgetItem(entry['notes'] or ""))
        
        data_table.resizeColumnsToContents()
        
        # 获取类型标签
        type_label = current_widget.property("type_label") or "语料"
        stats_label.setText(f"{type_label}总计: {len(entries)} 条")
    
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
        
        type_map = {
            "全部类型": None,
            "单词": "word",
            "单句": "sentence",
            "语篇": "discourse",
            "对话": "dialogue"
        }
        
        field = field_map[self.search_field_combo.currentText()]
        entry_type = type_map[self.search_type_combo.currentText()]
        results = self.db.search_entries(field, keyword, entry_type=entry_type)
        
        self.search_table.setRowCount(len(results))
        
        for row, entry in enumerate(results):
            self.search_table.setItem(row, 0, QTableWidgetItem(str(entry['id'])))
            self.search_table.setItem(row, 1, QTableWidgetItem(entry['example_id'] or ""))
            self.search_table.setItem(row, 2, QTableWidgetItem(entry['source_text'] or ""))
            self.search_table.setItem(row, 3, QTableWidgetItem(entry.get('source_text_cn', "") or ""))
            self.search_table.setItem(row, 4, QTableWidgetItem(entry['gloss'] or ""))
            self.search_table.setItem(row, 5, QTableWidgetItem(entry.get('gloss_cn', "") or ""))
            self.search_table.setItem(row, 6, QTableWidgetItem(entry['translation'] or ""))
            self.search_table.setItem(row, 7, QTableWidgetItem(entry.get('translation_cn', "") or ""))
            self.search_table.setItem(row, 8, QTableWidgetItem(entry['notes'] or ""))
        
        self.search_table.resizeColumnsToContents()
        self.search_stats_label.setText(f"搜索结果: {len(results)} 条")
        self.statusBar().showMessage(f"找到 {len(results)} 条匹配结果", 3000)
    
    def reset_search(self):
        """重置搜索"""
        self.search_input.clear()
        self.search_type_combo.setCurrentIndex(0)  # 重置为"全部类型"
        self.search_field_combo.setCurrentIndex(0)  # 重置为"全部字段"
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
    
    def _get_export_entries(self):
        """获取要导出的数据（根据类型筛选）"""
        type_map = {
            "全部类型": None,
            "单词": "word",
            "单句": "sentence",
            "语篇": "discourse",
            "对话": "dialogue"
        }
        
        selected_type = type_map[self.export_type_combo.currentText()]
        
        # 确定导出数据
        if self.export_selected_radio.isChecked() and self.search_table.rowCount() > 0:
            # 导出搜索结果
            entries = []
            for row in range(self.search_table.rowCount()):
                entry_id = int(self.search_table.item(row, 0).text())
                entry = self.db.get_entry(entry_id)
                if entry:
                    # 如果选择了特定类型，进行筛选
                    if selected_type is None or entry.get('entry_type') == selected_type:
                        entries.append(entry)
        else:
            # 导出所有语料（按类型筛选）
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
        
        # 获取格式参数
        show_numbering = self.show_numbering_checkbox.isChecked()
        include_chinese = self.include_chinese_checkbox.isChecked()
        group_by = self.export_group_by_checkbox.isChecked()
        
        # 生成格式化文本
        if group_by:
            # 按分组导出
            formatted_text = self._format_entries_by_group(entries, show_numbering, include_chinese)
        else:
            # 普通导出
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
    
    def _format_entries_by_group(self, entries, show_numbering=True, include_chinese=False):
        """按分组格式化输出"""
        # 按group_id分组
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
        
        # 生成格式化文本
        lines = []
        
        # 先输出分组数据
        for group_id in sorted(groups.keys()):
            group = groups[group_id]
            type_label = {"discourse": "语篇", "dialogue": "对话"}.get(group['type'], "分组")
            
            lines.append("=" * 60)
            lines.append(f"{type_label}: {group['name']} ({group_id})")
            lines.append(f"共 {len(group['entries'])} 句")
            lines.append("=" * 60)
            lines.append("")
            
            # 格式化该分组的所有条目
            group_text = TextFormatter.format_entries(
                group['entries'], 
                show_numbering, 
                include_chinese=include_chinese,
                font_config=self.font_config
            )
            lines.append(group_text)
            lines.append("")
        
        # 再输出未分组数据
        if ungrouped:
            lines.append("=" * 60)
            lines.append(f"未分组数据 (共 {len(ungrouped)} 条)")
            lines.append("=" * 60)
            lines.append("")
            ungrouped_text = TextFormatter.format_entries(
                ungrouped, 
                show_numbering, 
                include_chinese=include_chinese,
                font_config=self.font_config
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
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存Word文档", "", "Word Documents (*.docx)"
        )
        
        if not file_path:
            return
        
        # 获取要导出的数据
        entries = self._get_export_entries()
        
        if not entries:
            QMessageBox.warning(self, "提示", "没有可导出的语料！")
            return
        
        # 获取导出参数
        show_numbering = self.show_numbering_checkbox.isChecked()
        include_chinese = self.include_chinese_checkbox.isChecked()
        group_by = self.export_group_by_checkbox.isChecked()
        
        # 如果按分组导出，提示用户
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
        
        # 执行导出
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
        # 从当前Tab获取表格
        current_widget = self.data_sub_tabs.currentWidget()
        if not current_widget:
            return []
        
        data_table = current_widget.property("data_table")
        if not data_table:
            return []
        
        selected_rows = data_table.selectionModel().selectedRows()
        if not selected_rows:
            return []
        
        entries = []
        for index in selected_rows:
            row = index.row()
            entry_id = int(data_table.item(row, 0).text())
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
        
        # 从当前Tab获取导出选项
        current_widget = self.data_sub_tabs.currentWidget()
        if not current_widget:
            return
        
        data_show_numbering = current_widget.property("data_show_numbering")
        data_include_chinese = current_widget.property("data_include_chinese")
        
        show_numbering = data_show_numbering.isChecked() if data_show_numbering else True
        include_chinese = data_include_chinese.isChecked() if data_include_chinese else False
        
        formatted_text = TextFormatter.format_entries(
            entries, 
            show_numbering, 
            include_chinese=include_chinese,
            font_config=self.font_config
        )
        
        # 显示在对话框中
        dialog = QDialog(self)
        dialog.setWindowTitle(f"导出文本 ({len(entries)} 条)")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(formatted_text)
        text_edit.setReadOnly(True)
        for font_name in ["Consolas", "Monaco", "Menlo", "DejaVu Sans Mono", "Courier New", "monospace"]:
            font = QFont(font_name, 11)
            font.setStyleHint(QFont.StyleHint.Monospace)
            font.setFixedPitch(True)
            text_edit.setFont(font)
            if QFont(font_name).exactMatch():
                break
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
        
        # 从当前Tab获取导出选项
        current_widget = self.data_sub_tabs.currentWidget()
        if not current_widget:
            return
        
        data_show_numbering = current_widget.property("data_show_numbering")
        data_include_chinese = current_widget.property("data_include_chinese")
        
        show_numbering = data_show_numbering.isChecked() if data_show_numbering else True
        include_chinese = data_include_chinese.isChecked() if data_include_chinese else False
        
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
        # 获取当前Tab类型的所有语料
        entry_type = self.get_current_entry_type()
        entries = self.db.get_entries_by_type(entry_type)
        
        if not entries:
            current_widget = self.data_sub_tabs.currentWidget()
            type_label = current_widget.property("type_label") if current_widget else "语料"
            QMessageBox.warning(self, "提示", f"当前{type_label}Tab没有可导出的语料！")
            return
        
        # 从当前Tab获取导出选项
        current_widget = self.data_sub_tabs.currentWidget()
        if not current_widget:
            return
        
        data_show_numbering = current_widget.property("data_show_numbering")
        data_include_chinese = current_widget.property("data_include_chinese")
        
        show_numbering = data_show_numbering.isChecked() if data_show_numbering else True
        include_chinese = data_include_chinese.isChecked() if data_include_chinese else False
        
        formatted_text = TextFormatter.format_entries(
            entries, 
            show_numbering, 
            include_chinese=include_chinese,
            font_config=self.font_config
        )
        
        # 显示在对话框中
        dialog = QDialog(self)
        dialog.setWindowTitle(f"导出文本 (全部 {len(entries)} 条)")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(formatted_text)
        text_edit.setReadOnly(True)
        for font_name in ["Consolas", "Monaco", "Menlo", "DejaVu Sans Mono", "Courier New", "monospace"]:
            font = QFont(font_name, 11)
            font.setStyleHint(QFont.StyleHint.Monospace)
            font.setFixedPitch(True)
            text_edit.setFont(font)
            if QFont(font_name).exactMatch():
                break
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
    
    def quick_export_all_word(self):
        """快速导出当前Tab的所有语料到Word"""
        # 获取当前Tab类型的所有语料
        entry_type = self.get_current_entry_type()
        entries = self.db.get_entries_by_type(entry_type)
        
        if not entries:
            current_widget = self.data_sub_tabs.currentWidget()
            type_label = current_widget.property("type_label") if current_widget else "语料"
            QMessageBox.warning(self, "提示", f"当前{type_label}Tab没有可导出的语料！")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存Word文档", "", "Word Documents (*.docx)"
        )
        
        if not file_path:
            return
        
        # 从当前Tab获取导出选项
        current_widget = self.data_sub_tabs.currentWidget()
        if not current_widget:
            return
        
        data_show_numbering = current_widget.property("data_show_numbering")
        data_include_chinese = current_widget.property("data_include_chinese")
        
        show_numbering = data_show_numbering.isChecked() if data_show_numbering else True
        include_chinese = data_include_chinese.isChecked() if data_include_chinese else False
        
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
    
    def _copy_to_clipboard(self, text, dialog=None):
        """复制文本到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "复制成功", "文本已复制到剪贴板！")
        if dialog:
            dialog.close()
    
    def show_table_context_menu(self, pos):
        """显示表格右键菜单"""
        # 获取当前Tab的表格
        current_widget = self.data_sub_tabs.currentWidget()
        if not current_widget:
            return
        
        data_table = current_widget.property("data_table")
        if not data_table:
            return
        
        # 获取选中的行
        selected_rows = data_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        # 创建右键菜单
        menu = QMenu(self)
        
        # 获取选中行数
        selected_count = len(selected_rows)
        
        # 添加菜单项
        # 编辑操作
        edit_action = QAction(f"编辑 (加载到表单)", self)
        edit_action.triggered.connect(lambda: self.load_selected_entry_from_menu(data_table, selected_rows))
        menu.addAction(edit_action)
        
        menu.addSeparator()
        
        # 删除操作
        delete_action = QAction(f"删除选中项 ({selected_count} 条)", self)
        delete_action.triggered.connect(lambda: self.delete_selected_entries(data_table, selected_rows))
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        # 导出操作
        export_text_action = QAction(f"导出为文本 ({selected_count} 条)", self)
        export_text_action.triggered.connect(lambda: self.export_selected_to_text(data_table, selected_rows))
        menu.addAction(export_text_action)
        
        export_word_action = QAction(f"导出为Word ({selected_count} 条)", self)
        export_word_action.triggered.connect(lambda: self.export_selected_to_word(data_table, selected_rows))
        menu.addAction(export_word_action)
        
        menu.addSeparator()
        
        # 复制操作
        copy_action = QAction("复制单元格内容", self)
        copy_action.triggered.connect(lambda: self.copy_cell_content(data_table))
        menu.addAction(copy_action)
        
        # 显示菜单
        menu.exec(data_table.viewport().mapToGlobal(pos))
    
    def load_selected_entry_from_menu(self, data_table, selected_rows):
        """从右键菜单加载选中的条目到表单"""
        if not selected_rows:
            return
        
        # 只加载第一个选中的行
        first_row = selected_rows[0].row()
        self.load_entry_to_form(first_row, 0)
    
    def delete_selected_entries(self, data_table, selected_rows):
        """删除选中的多条语料"""
        if not selected_rows:
            return
        
        count = len(selected_rows)
        
        # 确认对话框
        reply = QMessageBox.question(
            self, 
            "确认删除", 
            f"确定要删除选中的 {count} 条语料吗？\n\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 获取所有选中的ID
                entry_ids = []
                for index in selected_rows:
                    row = index.row()
                    entry_id = int(data_table.item(row, 0).text())
                    entry_ids.append(entry_id)
                
                # 删除所有选中的条目
                deleted_count = 0
                for entry_id in entry_ids:
                    if self.db.delete_entry(entry_id):
                        deleted_count += 1
                
                QMessageBox.information(
                    self, 
                    "删除成功", 
                    f"成功删除 {deleted_count} 条语料！"
                )
                
                # 清空输入框并刷新表格
                self.clear_inputs()
                self.refresh_table()
                self.statusBar().showMessage(f"删除成功: {deleted_count} 条", 3000)
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")
    
    def export_selected_to_text(self, data_table, selected_rows):
        """导出选中的语料为文本"""
        if not selected_rows:
            return
        
        try:
            # 获取选中的条目
            entries = []
            for index in selected_rows:
                row = index.row()
                entry_id = int(data_table.item(row, 0).text())
                entry = self.db.get_entry(entry_id)
                if entry:
                    entries.append(entry)
            
            if not entries:
                QMessageBox.warning(self, "提示", "没有可导出的语料！")
                return
            
            # 从当前Tab获取导出选项
            current_widget = self.data_sub_tabs.currentWidget()
            if not current_widget:
                return
            
            data_show_numbering = current_widget.property("data_show_numbering")
            data_include_chinese = current_widget.property("data_include_chinese")
            
            show_numbering = data_show_numbering.isChecked() if data_show_numbering else True
            include_chinese = data_include_chinese.isChecked() if data_include_chinese else False
            
            formatted_text = TextFormatter.format_entries(
                entries, 
                show_numbering, 
                include_chinese=include_chinese,
                font_config=self.font_config
            )
            
            # 显示在对话框中
            dialog = QDialog(self)
            dialog.setWindowTitle(f"导出文本 ({len(entries)} 条)")
            dialog.setMinimumSize(800, 600)
            
            layout = QVBoxLayout()
            dialog.setLayout(layout)
            
            text_edit = QTextEdit()
            text_edit.setPlainText(formatted_text)
            text_edit.setReadOnly(True)
            for font_name in ["Consolas", "Monaco", "Menlo", "DejaVu Sans Mono", "Courier New", "monospace"]:
                font = QFont(font_name, 11)
                font.setStyleHint(QFont.StyleHint.Monospace)
                font.setFixedPitch(True)
                text_edit.setFont(font)
                if QFont(font_name).exactMatch():
                    break
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
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def export_selected_to_word(self, data_table, selected_rows):
        """导出选中的语料到Word"""
        if not selected_rows:
            return
        
        try:
            # 获取选中的条目
            entries = []
            for index in selected_rows:
                row = index.row()
                entry_id = int(data_table.item(row, 0).text())
                entry = self.db.get_entry(entry_id)
                if entry:
                    entries.append(entry)
            
            if not entries:
                QMessageBox.warning(self, "提示", "没有可导出的语料！")
                return
            
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存Word文档", "", "Word Documents (*.docx)"
            )
            
            if not file_path:
                return
            
            # 从当前Tab获取导出选项
            current_widget = self.data_sub_tabs.currentWidget()
            if not current_widget:
                return
            
            data_show_numbering = current_widget.property("data_show_numbering")
            data_include_chinese = current_widget.property("data_include_chinese")
            
            show_numbering = data_show_numbering.isChecked() if data_show_numbering else True
            include_chinese = data_include_chinese.isChecked() if data_include_chinese else False
            
            # 导出
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
    
    def load_font_config(self):
        """加载字体配置"""
        config_path = os.path.join(os.path.expanduser("~"), ".fieldnote", "font_config.json")
        default_config = {
            "source_text": "Doulos SIL Compact",
            "source_text_size": 12,
            "gloss": "Charis SIL Compact",
            "gloss_size": 11,
            "translation": "系统默认",
            "translation_size": 11,
            "chinese": "系统默认",
            "chinese_size": 10
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置，确保所有键都存在
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
        except Exception as e:
            print(f"加载字体配置失败: {e}")
        
        return default_config
    
    def save_font_config(self):
        """保存字体配置"""
        config_path = os.path.join(os.path.expanduser("~"), ".fieldnote", "font_config.json")
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.font_config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"保存字体配置失败: {str(e)}")
    
    def apply_fonts(self):
        """应用字体设置到所有Tab的输入框"""
        # 原文字体
        source_font = self.font_config.get("source_text", "Doulos SIL Compact")
        source_size = self.font_config.get("source_text_size", 12)
        
        # 词汇分解字体
        gloss_font = self.font_config.get("gloss", "Charis SIL Compact")
        gloss_size = self.font_config.get("gloss_size", 11)
        
        # 翻译字体
        translation_font = self.font_config.get("translation", "系统默认")
        translation_size = self.font_config.get("translation_size", 11)
        
        # 汉字字段字体
        chinese_font = self.font_config.get("chinese", "系统默认")
        chinese_size = self.font_config.get("chinese_size", 10)
        
        # 遍历所有Tab并应用字体
        for tab_index in range(self.data_sub_tabs.count()):
            tab_widget = self.data_sub_tabs.widget(tab_index)
            if not tab_widget:
                continue
            
            # 获取该Tab的输入框
            source_text_input = tab_widget.property("source_text_input")
            source_text_cn_input = tab_widget.property("source_text_cn_input")
            gloss_input = tab_widget.property("gloss_input")
            gloss_cn_input = tab_widget.property("gloss_cn_input")
            translation_input = tab_widget.property("translation_input")
            translation_cn_input = tab_widget.property("translation_cn_input")
            
            # 应用原文字体
            if source_text_input and source_font != "系统默认":
                source_text_input.setFont(QFont(source_font, source_size))
            
            # 应用词汇分解字体
            if gloss_input and gloss_font != "系统默认":
                gloss_input.setFont(QFont(gloss_font, gloss_size))
            
            # 应用翻译字体
            if translation_input and translation_font != "系统默认":
                translation_input.setFont(QFont(translation_font, translation_size))
            
            # 应用汉字字段字体
            if chinese_font != "系统默认":
                if source_text_cn_input:
                    source_text_cn_input.setFont(QFont(chinese_font, chinese_size))
                if gloss_cn_input:
                    gloss_cn_input.setFont(QFont(chinese_font, chinese_size))
                if translation_cn_input:
                    translation_cn_input.setFont(QFont(chinese_font, chinese_size))
    
    def open_font_settings(self):
        """打开字体设置对话框"""
        dialog = FontSettingsDialog(self, self.font_config)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.font_config = dialog.get_config()
            self.save_font_config()
            self.apply_fonts()
            QMessageBox.information(self, "成功", "字体设置已应用！")
    
    def setup_global_shortcuts(self):
        """设置全局快捷键（绑定到主窗口）"""
        # 转为大写
        shortcut_upper = QShortcut(QKeySequence("Ctrl+Shift+U"), self)
        shortcut_upper.activated.connect(lambda: self.transform_focused_text('upper'))
        
        # 转为小写
        shortcut_lower = QShortcut(QKeySequence("Ctrl+Shift+L"), self)
        shortcut_lower.activated.connect(lambda: self.transform_focused_text('lower'))
        
        # 首字母大写
        shortcut_title = QShortcut(QKeySequence("Ctrl+Shift+T"), self)
        shortcut_title.activated.connect(lambda: self.transform_focused_text('title'))
        
        # 小型大写
        shortcut_small_caps = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
        shortcut_small_caps.activated.connect(lambda: self.transform_focused_text('small_caps'))
    
    def setup_text_edit_context_menu(self, text_edit):
        """为文本编辑框设置右键菜单"""
        text_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        text_edit.customContextMenuRequested.connect(
            lambda pos: self.show_text_edit_context_menu(text_edit, pos)
        )
    
    def show_text_edit_context_menu(self, text_edit, pos):
        """显示文本编辑框的右键菜单"""
        menu = text_edit.createStandardContextMenu()
        
        # 如果有选中文本，添加大小写转换选项
        if text_edit.textCursor().hasSelection():
            menu.addSeparator()
            
            # 检测操作系统，显示正确的快捷键提示
            import platform
            modifier_key = "Cmd" if platform.system() == "Darwin" else "Ctrl"
            
            # 全部大写（用于语法标签，如 NOM, ACC, PST）
            upper_action = QAction(f"转为大写 (NOM)\t{modifier_key}+Shift+U", self)
            upper_action.triggered.connect(lambda: self.transform_selected_text(text_edit, 'upper'))
            menu.addAction(upper_action)
            
            # 全部小写
            lower_action = QAction(f"转为小写 (nom)\t{modifier_key}+Shift+L", self)
            lower_action.triggered.connect(lambda: self.transform_selected_text(text_edit, 'lower'))
            menu.addAction(lower_action)
            
            # 首字母大写
            title_action = QAction(f"首字母大写 (Nom)\t{modifier_key}+Shift+T", self)
            title_action.triggered.connect(lambda: self.transform_selected_text(text_edit, 'title'))
            menu.addAction(title_action)
            
            # 小型大写（转为Unicode小型大写字母）
            small_caps_action = QAction(f"小型大写 (ɴᴏᴍ)\t{modifier_key}+Shift+C", self)
            small_caps_action.triggered.connect(lambda: self.transform_selected_text(text_edit, 'small_caps'))
            menu.addAction(small_caps_action)
        
        menu.exec(text_edit.mapToGlobal(pos))
    
    def transform_focused_text(self, transform_type):
        """转换当前焦点输入框中选中的文本"""
        # 获取当前焦点widget
        focused_widget = QApplication.focusWidget()
        
        # 检查是否是 QTextEdit
        if isinstance(focused_widget, QTextEdit):
            self.transform_selected_text(focused_widget, transform_type)
    
    def transform_selected_text(self, text_edit, transform_type):
        """转换选中的文本"""
        cursor = text_edit.textCursor()
        if not cursor.hasSelection():
            return
        
        selected_text = cursor.selectedText()
        
        if transform_type == 'upper':
            transformed = selected_text.upper()
        elif transform_type == 'lower':
            transformed = selected_text.lower()
        elif transform_type == 'title':
            transformed = selected_text.title()
        elif transform_type == 'small_caps':
            # 转换为Unicode小型大写字母
            transformed = self.to_small_caps(selected_text)
        else:
            return
        
        cursor.insertText(transformed)
    
    def to_small_caps(self, text):
        """将文本转换为Unicode小型大写字母"""
        # Unicode小型大写字母映射表
        small_caps_map = {
            'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ꜰ', 'G': 'ɢ', 'H': 'ʜ',
            'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ', 'O': 'ᴏ', 'P': 'ᴘ',
            'Q': 'ǫ', 'R': 'ʀ', 'S': 'ꜱ', 'T': 'ᴛ', 'U': 'ᴜ', 'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x',
            'Y': 'ʏ', 'Z': 'ᴢ',
            'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ', 'h': 'ʜ',
            'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ',
            'q': 'ǫ', 'r': 'ʀ', 's': 'ꜱ', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x',
            'y': 'ʏ', 'z': 'ᴢ'
        }
        
        result = []
        for char in text:
            result.append(small_caps_map.get(char, char))
        
        return ''.join(result)
    
    def closeEvent(self, event):
        """关闭事件处理"""
        self.db.close()
        event.accept()


class FontSettingsDialog(QDialog):
    """字体设置对话框"""
    
    def __init__(self, parent, current_config):
        super().__init__(parent)
        self.current_config = current_config.copy()
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("字体设置")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 说明文本
        info_label = QLabel(
            "为不同字段设置专用字体（如Doulos SIL Compact用于IPA符号）\n"
            "字体必须已安装在系统中才能生效"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addSpacing(10)
        
        # 字体设置表单
        form_layout = QFormLayout()
        
        # 原文字段
        source_layout = QHBoxLayout()
        self.source_font_combo = self.create_font_combo()
        self.source_font_combo.setCurrentText(self.current_config.get("source_text", "Doulos SIL Compact"))
        self.source_size_spin = QSpinBox()
        self.source_size_spin.setRange(8, 24)
        self.source_size_spin.setValue(self.current_config.get("source_text_size", 12))
        source_layout.addWidget(self.source_font_combo, 3)
        source_layout.addWidget(QLabel("大小:"))
        source_layout.addWidget(self.source_size_spin, 1)
        form_layout.addRow("原文字体:", source_layout)
        
        # 词汇分解字段
        gloss_layout = QHBoxLayout()
        self.gloss_font_combo = self.create_font_combo()
        self.gloss_font_combo.setCurrentText(self.current_config.get("gloss", "Charis SIL Compact"))
        self.gloss_size_spin = QSpinBox()
        self.gloss_size_spin.setRange(8, 24)
        self.gloss_size_spin.setValue(self.current_config.get("gloss_size", 11))
        gloss_layout.addWidget(self.gloss_font_combo, 3)
        gloss_layout.addWidget(QLabel("大小:"))
        gloss_layout.addWidget(self.gloss_size_spin, 1)
        form_layout.addRow("词汇分解字体:", gloss_layout)
        
        # 翻译字段
        translation_layout = QHBoxLayout()
        self.translation_font_combo = self.create_font_combo()
        self.translation_font_combo.setCurrentText(self.current_config.get("translation", "系统默认"))
        self.translation_size_spin = QSpinBox()
        self.translation_size_spin.setRange(8, 24)
        self.translation_size_spin.setValue(self.current_config.get("translation_size", 11))
        translation_layout.addWidget(self.translation_font_combo, 3)
        translation_layout.addWidget(QLabel("大小:"))
        translation_layout.addWidget(self.translation_size_spin, 1)
        form_layout.addRow("翻译字体:", translation_layout)
        
        # 汉字字段
        chinese_layout = QHBoxLayout()
        self.chinese_font_combo = self.create_font_combo()
        self.chinese_font_combo.setCurrentText(self.current_config.get("chinese", "系统默认"))
        self.chinese_size_spin = QSpinBox()
        self.chinese_size_spin.setRange(8, 24)
        self.chinese_size_spin.setValue(self.current_config.get("chinese_size", 10))
        chinese_layout.addWidget(self.chinese_font_combo, 3)
        chinese_layout.addWidget(QLabel("大小:"))
        chinese_layout.addWidget(self.chinese_size_spin, 1)
        form_layout.addRow("汉字字体:", chinese_layout)
        
        layout.addLayout(form_layout)
        
        layout.addSpacing(10)
        
        # 预览区域
        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout()
        preview_group.setLayout(preview_layout)
        
        self.preview_label = QLabel("The quick brown fox jumps over the lazy dog\nɑ ɔ ə ʃ ʒ θ ð ŋ 测试汉字")
        self.preview_label.setWordWrap(True)
        preview_layout.addWidget(self.preview_label)
        
        preview_btn = QPushButton("预览当前设置")
        preview_btn.clicked.connect(self.update_preview)
        preview_layout.addWidget(preview_btn)
        
        layout.addWidget(preview_group)
        
        layout.addSpacing(10)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        reset_btn = QPushButton("恢复默认")
        reset_btn.clicked.connect(self.reset_to_default)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def create_font_combo(self):
        """创建字体选择下拉框"""
        combo = QComboBox()
        combo.setEditable(True)  # 允许输入自定义字体名
        
        # 添加常用语言学字体和中文字体
        fonts = [
            "系统默认",
            "Doulos SIL Compact",
            "Doulos SIL",
            "Charis SIL Compact",
            "Charis SIL",
            "Gentium Plus",
            "Gentium Basic",
            "DejaVu Sans",
            "Arial Unicode MS",
            "Lucida Sans Unicode",
            "Times New Roman",
            "Courier New",
            "宋体",
            "Songti SC",
            "SimSun",
            "黑体",
            "Heiti SC",
            "SimHei",
            "楷体",
            "Kaiti SC",
            "微软雅黑",
            "Microsoft YaHei"
        ]
        
        combo.addItems(fonts)
        return combo
    
    def update_preview(self):
        """更新预览"""
        font_name = self.source_font_combo.currentText()
        font_size = self.source_size_spin.value()
        
        if font_name != "系统默认":
            self.preview_label.setFont(QFont(font_name, font_size))
        else:
            self.preview_label.setFont(QFont())
    
    def reset_to_default(self):
        """恢复默认设置"""
        self.source_font_combo.setCurrentText("Doulos SIL Compact")
        self.source_size_spin.setValue(12)
        self.gloss_font_combo.setCurrentText("Charis SIL Compact")
        self.gloss_size_spin.setValue(11)
        self.translation_font_combo.setCurrentText("系统默认")
        self.translation_size_spin.setValue(11)
        self.chinese_font_combo.setCurrentText("系统默认")
        self.chinese_size_spin.setValue(10)
    
    def get_config(self):
        """获取配置"""
        return {
            "source_text": self.source_font_combo.currentText(),
            "source_text_size": self.source_size_spin.value(),
            "gloss": self.gloss_font_combo.currentText(),
            "gloss_size": self.gloss_size_spin.value(),
            "translation": self.translation_font_combo.currentText(),
            "translation_size": self.translation_size_spin.value(),
            "chinese": self.chinese_font_combo.currentText(),
            "chinese_size": self.chinese_size_spin.value()
        }

