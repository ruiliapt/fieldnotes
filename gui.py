"""
图形界面模块 - 使用PyQt6实现
"""
import sys
import json
import csv
import logging
import difflib
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QMessageBox, QFileDialog, QDialog, QFormLayout, QSpinBox,
    QDoubleSpinBox, QCheckBox, QComboBox, QTabWidget, QGroupBox, QApplication,
    QMenu, QScrollArea, QProgressBar, QSizePolicy, QFrame, QSplitter,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QAction, QShortcut, QKeySequence, QBrush, QColor, QTextDocument
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter

from database import CorpusDatabase
from exporter import WordExporter, TextFormatter
from theme import ThemeManager
import os
import base64

logger = logging.getLogger(__name__)

# 表格列常量
COL_ID = 0
COL_EXAMPLE_ID = 1
COL_SOURCE_TEXT = 2
COL_SOURCE_TEXT_CN = 3
COL_GLOSS = 4
COL_GLOSS_CN = 5
COL_TRANSLATION = 6
COL_TRANSLATION_CN = 7
COL_NOTES = 8
COL_CREATED_AT = 9
COL_TAGS = 10


def _get_monospace_font(size: int = 11) -> QFont:
    """获取等宽字体，按优先级尝试"""
    for name in ["Consolas", "Monaco", "Menlo", "DejaVu Sans Mono", "Courier New"]:
        font = QFont(name, size)
        if QFont(name).exactMatch():
            font.setStyleHint(QFont.StyleHint.Monospace)
            font.setFixedPitch(True)
            return font
    font = QFont("monospace", size)
    font.setStyleHint(QFont.StyleHint.Monospace)
    font.setFixedPitch(True)
    return font


class IPAToolbarWidget(QWidget):
    """可折叠的IPA符号插入工具栏"""
    symbol_clicked = pyqtSignal(str)

    IPA_CATEGORIES = {
        "元音": "ɑ æ ɛ ə ɪ ɨ ɯ ɔ ø œ ʊ ʌ ɶ ɐ ɒ ɜ ɘ ɤ ɵ ʉ ʏ",
        "辅音": "ŋ ɲ ɴ ʔ β ɸ θ ð ʃ ʒ ɕ ʑ ʂ ʐ ɣ χ ʁ ɦ ɬ ɹ ɻ ɭ ʀ ʋ ɟ ɠ ɗ ɓ",
        "声调": "˥ ˦ ˧ ˨ ˩ ↗ ↘ → ˥˩ ˧˥ ˩˥ ˨˩ ↑ ↓",
        "上标": "⁰ ¹ ² ³ ⁴ ⁵ ⁶ ⁷ ⁸ ⁹",
        "变音符": "ʰ ʷ ʲ ʼ ̃ ̈ ̥ ̤ ̰ ̬ ̯",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._expanded = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.setLayout(layout)

        # 折叠按钮
        self.toggle_btn = QPushButton("▶ IPA符号")
        self.toggle_btn.clicked.connect(self._toggle)
        layout.addWidget(self.toggle_btn)

        # 内容区（默认隐藏）
        self.content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)
        self.content_widget.setLayout(content_layout)

        for category, symbols_str in self.IPA_CATEGORIES.items():
            row_layout = QHBoxLayout()
            row_layout.setSpacing(2)
            label = QLabel(f"{category}:")
            label.setFixedWidth(48)
            row_layout.addWidget(label)

            symbols = symbols_str.split()
            for symbol in symbols:
                btn = QPushButton(symbol)
                btn.setFixedSize(30, 26)
                btn.clicked.connect(lambda checked, s=symbol: self.symbol_clicked.emit(s))
                row_layout.addWidget(btn)

            row_layout.addStretch()
            content_layout.addLayout(row_layout)

        self.content_widget.setVisible(False)
        layout.addWidget(self.content_widget)

    def _toggle(self):
        self._expanded = not self._expanded
        self.content_widget.setVisible(self._expanded)
        self.toggle_btn.setText("▼ IPA符号" if self._expanded else "▶ IPA符号")


class TagSelectorWidget(QWidget):
    """标签多选组件：预设标签复选框 + 自定义输入"""
    PREDEFINED_TAGS = {
        "句型": ["陈述句", "疑问句", "祈使句", "感叹句"],
        "话题": ["问候", "饮食", "家庭", "天气"],
        "语法": ["被动", "使役", "否定", "疑问"],
        "质量": ["已审核", "待审核", "存疑", "定稿"],
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checkboxes: dict[str, QCheckBox] = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.setLayout(layout)

        for category, tags in self.PREDEFINED_TAGS.items():
            row = QHBoxLayout()
            row.setSpacing(4)
            cat_label = QLabel(f"{category}:")
            cat_label.setFixedWidth(40)
            row.addWidget(cat_label)
            for tag in tags:
                cb = QCheckBox(tag)
                self._checkboxes[tag] = cb
                row.addWidget(cb)
            row.addStretch()
            layout.addLayout(row)

        # 自定义标签输入
        custom_row = QHBoxLayout()
        custom_row.setSpacing(4)
        custom_label = QLabel("自定义:")
        custom_label.setFixedWidth(40)
        custom_row.addWidget(custom_label)
        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("输入自定义标签，逗号分隔")
        custom_row.addWidget(self.custom_input)
        layout.addLayout(custom_row)

    def get_tags(self) -> list[str]:
        """返回选中的标签列表"""
        tags = []
        for tag, cb in self._checkboxes.items():
            if cb.isChecked():
                tags.append(tag)
        # 自定义标签
        custom = self.custom_input.text().strip()
        if custom:
            for t in custom.split(','):
                t = t.strip()
                if t and t not in tags:
                    tags.append(t)
        return tags

    def set_tags(self, tags: list[str]):
        """设置选中状态"""
        # 先清空
        self.clear()
        predefined = set()
        custom_tags = []
        for tag in tags:
            tag = tag.strip()
            if not tag:
                continue
            if tag in self._checkboxes:
                self._checkboxes[tag].setChecked(True)
                predefined.add(tag)
            else:
                custom_tags.append(tag)
        if custom_tags:
            self.custom_input.setText(', '.join(custom_tags))

    def clear(self):
        """清空所有选中"""
        for cb in self._checkboxes.values():
            cb.setChecked(False)
        self.custom_input.clear()


class EntryTabWidget(QWidget):
    """单个条目类型（word/sentence/discourse/dialogue）的Tab组件"""

    def __init__(self, entry_type: str, type_label: str, main_window, parent=None):
        super().__init__(parent)
        self.entry_type = entry_type
        self.type_label = type_label
        self.main_window = main_window

        # 表单组件
        self.example_id_input: QLineEdit = None
        self.source_text_input: QTextEdit = None
        self.source_text_cn_input: QTextEdit = None
        self.gloss_input: QTextEdit = None
        self.gloss_cn_input: QTextEdit = None
        self.translation_input: QTextEdit = None
        self.translation_cn_input: QTextEdit = None
        self.notes_input: QTextEdit = None
        self.tag_selector: TagSelectorWidget = None
        self.ipa_toolbar: IPAToolbarWidget = None
        self.data_table: QTableWidget = None
        self.stats_label: QLabel = None
        self.data_show_numbering: QCheckBox = None
        self.data_include_chinese: QCheckBox = None
        self.validation_label: QLabel = None
        self.group_combo: QComboBox = None

        self._build_ui()

    def _build_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # ===== 左侧：录入区域 =====
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        left_widget.setMaximumWidth(500)

        # IPA 工具栏
        self.ipa_toolbar = IPAToolbarWidget()
        self.ipa_toolbar.symbol_clicked.connect(self._insert_ipa_symbol)
        left_layout.addWidget(self.ipa_toolbar)

        # 输入区域
        input_group = QGroupBox("语料录入")
        input_layout = QFormLayout()
        input_group.setLayout(input_layout)

        # 例句编号
        self.example_id_input = QLineEdit()
        self.example_id_input.setPlaceholderText("例：CJ001")
        input_layout.addRow("例句编号:", self.example_id_input)

        # 语篇/对话：分组选择
        if self.entry_type in ["discourse", "dialogue"]:
            group_label = "所属语篇:" if self.entry_type == "discourse" else "所属对话:"
            group_select_layout = QHBoxLayout()

            self.group_combo = QComboBox()
            self.group_combo.setEditable(False)
            self.group_combo.setMinimumWidth(200)
            group_select_layout.addWidget(self.group_combo, 1)

            new_group_btn = QPushButton("新建")
            new_group_btn.setMaximumWidth(60)
            new_group_btn.clicked.connect(
                lambda: self.main_window.create_new_group(self.entry_type)
            )
            group_select_layout.addWidget(new_group_btn)

            refresh_group_btn = QPushButton("刷新")
            refresh_group_btn.setMaximumWidth(60)
            refresh_group_btn.clicked.connect(
                lambda: self.main_window.refresh_group_list(self.entry_type)
            )
            group_select_layout.addWidget(refresh_group_btn)

            input_layout.addRow(group_label, group_select_layout)

        # 原文
        self.source_text_input = QTextEdit()
        self.source_text_input.setMaximumHeight(60)
        self.source_text_input.setPlaceholderText("输入原文（支持IPA和Unicode字符）")
        self.main_window.setup_text_edit_context_menu(self.source_text_input)
        input_layout.addRow("原文:", self.source_text_input)

        # 原文(汉字)
        self.source_text_cn_input = QTextEdit()
        self.source_text_cn_input.setMaximumHeight(60)
        self.source_text_cn_input.setPlaceholderText("输入原文的汉字注释（可选）")
        self.main_window.setup_text_edit_context_menu(self.source_text_cn_input)
        input_layout.addRow("原文(汉字):", self.source_text_cn_input)

        # 词汇分解（带 AI 按钮）
        self.gloss_input = QTextEdit()
        self.gloss_input.setMaximumHeight(60)
        self.gloss_input.setPlaceholderText("输入词汇分解/注释")
        self.main_window.setup_text_edit_context_menu(self.gloss_input)
        gloss_row_layout = QHBoxLayout()
        gloss_row_layout.setSpacing(4)
        gloss_row_layout.addWidget(self.gloss_input)
        self.ai_gloss_btn = QPushButton("AI分析")
        self.ai_gloss_btn.setFixedWidth(60)
        self.ai_gloss_btn.setToolTip("使用 AI 自动生成词汇分解")
        self.ai_gloss_btn.clicked.connect(self.main_window.ai_auto_gloss)
        gloss_row_layout.addWidget(self.ai_gloss_btn)
        input_layout.addRow("词汇分解:", gloss_row_layout)

        # 词汇分解(汉字)
        self.gloss_cn_input = QTextEdit()
        self.gloss_cn_input.setMaximumHeight(60)
        self.gloss_cn_input.setPlaceholderText("输入词汇分解的汉字注释（可选）")
        self.main_window.setup_text_edit_context_menu(self.gloss_cn_input)
        input_layout.addRow("词汇分解(汉字):", self.gloss_cn_input)

        # 翻译（带 AI 按钮）
        self.translation_input = QTextEdit()
        self.translation_input.setMaximumHeight(60)
        self.translation_input.setPlaceholderText("输入翻译")
        self.main_window.setup_text_edit_context_menu(self.translation_input)
        trans_row_layout = QHBoxLayout()
        trans_row_layout.setSpacing(4)
        trans_row_layout.addWidget(self.translation_input)
        self.ai_translate_btn = QPushButton("AI翻译")
        self.ai_translate_btn.setFixedWidth(60)
        self.ai_translate_btn.setToolTip("使用 AI 自动翻译")
        self.ai_translate_btn.clicked.connect(self.main_window.ai_auto_translate)
        trans_row_layout.addWidget(self.ai_translate_btn)
        input_layout.addRow("翻译:", trans_row_layout)

        # 翻译(汉字)
        self.translation_cn_input = QTextEdit()
        self.translation_cn_input.setMaximumHeight(60)
        self.translation_cn_input.setPlaceholderText("输入翻译的汉字版本（可选）")
        self.main_window.setup_text_edit_context_menu(self.translation_cn_input)
        input_layout.addRow("翻译(汉字):", self.translation_cn_input)

        # 备注
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText("输入备注（可选）")
        self.main_window.setup_text_edit_context_menu(self.notes_input)
        input_layout.addRow("备注:", self.notes_input)

        # 标签选择器
        self.tag_selector = TagSelectorWidget()
        input_layout.addRow("标签:", self.tag_selector)

        left_layout.addWidget(input_group)

        # 验证标签
        self.validation_label = QLabel("")
        self.validation_label.setWordWrap(True)
        left_layout.addWidget(self.validation_label)

        # 按钮区域
        button_group = QGroupBox("操作")
        button_group_layout = QVBoxLayout()
        button_group.setLayout(button_group_layout)

        add_btn = QPushButton("添加语料")
        add_btn.clicked.connect(self.main_window.add_entry)
        button_group_layout.addWidget(add_btn)

        update_btn = QPushButton("更新语料")
        update_btn.clicked.connect(self.main_window.update_entry)
        button_group_layout.addWidget(update_btn)

        delete_btn = QPushButton("删除语料")
        delete_btn.clicked.connect(self.main_window.delete_entry)
        button_group_layout.addWidget(delete_btn)

        clear_btn = QPushButton("清空输入")
        clear_btn.clicked.connect(self.main_window.clear_inputs)
        button_group_layout.addWidget(clear_btn)

        import_btn = QPushButton("批量导入")
        import_btn.clicked.connect(self.main_window.import_data)
        button_group_layout.addWidget(import_btn)

        left_layout.addWidget(button_group)
        left_layout.addStretch()

        # ===== 右侧：数据列表区域 =====
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)

        # 数据表格
        list_group = QGroupBox("已录入语料")
        list_layout = QVBoxLayout()
        list_group.setLayout(list_layout)

        self.data_table = QTableWidget()
        self.data_table.setColumnCount(11)
        self.data_table.setHorizontalHeaderLabels(
            ["ID", "例句编号", "原文", "原文(汉字)", "词汇分解",
             "词汇分解(汉字)", "翻译", "翻译(汉字)", "备注", "创建时间", "标签"]
        )
        self.data_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.data_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.data_table.setAlternatingRowColors(True)
        self.data_table.cellClicked.connect(self.main_window.load_entry_to_form)
        self.data_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.data_table.customContextMenuRequested.connect(self.main_window.show_table_context_menu)
        list_layout.addWidget(self.data_table)

        # 统计信息
        self.stats_label = QLabel("总计: 0 条语料")
        list_layout.addWidget(self.stats_label)

        right_layout.addWidget(list_group)

        # ===== 导出控制区域 =====
        export_group = QGroupBox("快速导出")
        export_layout = QVBoxLayout()
        export_group.setLayout(export_layout)

        options_layout = QHBoxLayout()

        self.data_show_numbering = QCheckBox("显示编号")
        self.data_show_numbering.setChecked(True)
        options_layout.addWidget(self.data_show_numbering)

        self.data_include_chinese = QCheckBox("包含汉字")
        self.data_include_chinese.setChecked(False)
        options_layout.addWidget(self.data_include_chinese)

        options_layout.addStretch()
        export_layout.addLayout(options_layout)

        # 导出按钮
        export_buttons_layout = QHBoxLayout()

        export_text_btn = QPushButton("生成文本")
        export_text_btn.setToolTip("将选中的语料生成对齐文本")
        export_text_btn.clicked.connect(self.main_window.quick_export_text)
        export_buttons_layout.addWidget(export_text_btn)

        export_word_btn = QPushButton("导出Word")
        export_word_btn.setToolTip("将选中的语料导出到Word文档")
        export_word_btn.clicked.connect(self.main_window.quick_export_word)
        export_buttons_layout.addWidget(export_word_btn)

        export_all_text_btn = QPushButton("全部文本")
        export_all_text_btn.setToolTip("将所有语料生成对齐文本")
        export_all_text_btn.clicked.connect(self.main_window.quick_export_all_text)
        export_buttons_layout.addWidget(export_all_text_btn)

        export_all_word_btn = QPushButton("全部Word")
        export_all_word_btn.setToolTip("将所有语料导出到Word文档")
        export_all_word_btn.clicked.connect(self.main_window.quick_export_all_word)
        export_buttons_layout.addWidget(export_all_word_btn)

        export_csv_btn = QPushButton("导出CSV")
        export_csv_btn.setToolTip("将所有语料导出为CSV文件")
        export_csv_btn.clicked.connect(self.main_window.export_to_csv)
        export_buttons_layout.addWidget(export_csv_btn)

        export_json_btn = QPushButton("导出JSON")
        export_json_btn.setToolTip("将所有语料导出为JSON文件")
        export_json_btn.clicked.connect(self.main_window.export_to_json)
        export_buttons_layout.addWidget(export_json_btn)

        export_layout.addLayout(export_buttons_layout)

        right_layout.addWidget(export_group)

        # 将左右两侧添加到主布局
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)

    def _insert_ipa_symbol(self, symbol: str):
        """将IPA符号插入到当前获得焦点的文本框"""
        focused = QApplication.focusWidget()
        if isinstance(focused, QTextEdit):
            focused.insertPlainText(symbol)


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.db = CorpusDatabase()
        self.exporter = WordExporter()
        self.current_entry_id = None

        # 主题管理
        self.theme_manager = ThemeManager(self.load_theme_preference())

        # 加载字体配置
        self.font_config = self.load_font_config()

        # AI 管理器
        self.ai_manager = None
        self._ai_worker = None
        self._init_ai_manager()

        self.init_ui()
        self.apply_theme()
        self.apply_fonts()
        self.setup_global_shortcuts()
        self.refresh_table()
        self.restore_window_state()
        self.auto_backup_on_startup()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("Fieldnotes Lite v0.6.0 - 田野笔记管理工具")
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
        self.main_tab_widget = QTabWidget()
        main_layout.addWidget(self.main_tab_widget)

        # 数据管理标签页
        data_tab = self.create_data_tab()
        self.main_tab_widget.addTab(data_tab, "数据管理")

        # 检索标签页
        search_tab = self.create_search_tab()
        self.main_tab_widget.addTab(search_tab, "检索")

        # 导出标签页
        export_tab = self.create_export_tab()
        self.main_tab_widget.addTab(export_tab, "导出")

        # 统计标签页
        stats_tab = self.create_stats_tab()
        self.main_tab_widget.addTab(stats_tab, "统计")

        # 切换到统计Tab时自动刷新
        self.main_tab_widget.currentChanged.connect(self._on_main_tab_changed)

        # 状态栏
        self.update_status_bar()

    def _on_main_tab_changed(self, index):
        """主Tab切换时的处理"""
        if self.main_tab_widget.tabText(index) == "统计":
            self.refresh_stats()

    def _get_current_tab(self) -> 'EntryTabWidget | None':
        """获取当前选中的 EntryTabWidget"""
        widget = self.data_sub_tabs.currentWidget()
        if isinstance(widget, EntryTabWidget):
            return widget
        return None

    def create_data_tab(self):
        """创建数据管理标签页（包含4个子Tab）"""
        widget = QWidget()
        main_layout = QVBoxLayout()
        widget.setLayout(main_layout)

        # 创建子Tab容器
        self.data_sub_tabs = QTabWidget()
        main_layout.addWidget(self.data_sub_tabs)

        # 创建4个子Tab
        self.word_tab = EntryTabWidget("word", "单词", self)
        self.sentence_tab = EntryTabWidget("sentence", "单句", self)
        self.discourse_tab = EntryTabWidget("discourse", "语篇", self)
        self.dialogue_tab = EntryTabWidget("dialogue", "对话", self)

        self.data_sub_tabs.addTab(self.word_tab, "单词")
        self.data_sub_tabs.addTab(self.sentence_tab, "单句")
        self.data_sub_tabs.addTab(self.discourse_tab, "语篇")
        self.data_sub_tabs.addTab(self.dialogue_tab, "对话")

        # 初始加载分组列表
        self.refresh_group_list("discourse")
        self.refresh_group_list("dialogue")

        # 当Tab切换时刷新表格
        self.data_sub_tabs.currentChanged.connect(lambda: self.refresh_table())

        return widget

    def get_current_entry_type(self):
        """获取当前选中Tab的条目类型"""
        tab = self._get_current_tab()
        if tab:
            return tab.entry_type
        return "sentence"

    def refresh_group_list(self, entry_type):
        """刷新语篇/对话列表"""
        combo = None
        if entry_type == "discourse":
            combo = self.discourse_tab.group_combo
        elif entry_type == "dialogue":
            combo = self.dialogue_tab.group_combo

        if not combo:
            return

        # 清空并重新加载
        combo.clear()
        combo.addItem("--- 请选择 ---", None)

        # 从数据库获取分组列表
        groups = self.db.get_groups_by_type(entry_type)

        for group in groups:
            display_text = f"{group['group_id']} - {group['group_name']} ({group['count']}句)"
            combo.addItem(display_text, (group['group_id'], group['group_name']))

    def create_new_group(self, entry_type):
        """创建新的语篇/对话分组"""
        from PyQt6.QtWidgets import QInputDialog

        type_label = "语篇" if entry_type == "discourse" else "对话"

        group_name, ok = QInputDialog.getText(
            self,
            f"新建{type_label}",
            f"请输入{type_label}名称:",
            QLineEdit.EchoMode.Normal,
            ""
        )

        if ok and group_name.strip():
            group_name = group_name.strip()
            group_id = self.db.get_next_group_id(entry_type)

            QMessageBox.information(
                self,
                "成功",
                f"已创建{type_label}: {group_id} - {group_name}\n\n"
                f"现在可以在下拉框中选择该{type_label}，然后录入句子。"
            )

            self.refresh_group_list(entry_type)

            # 在combo box中选中新创建的分组
            combo = None
            if entry_type == "discourse":
                combo = self.discourse_tab.group_combo
            elif entry_type == "dialogue":
                combo = self.dialogue_tab.group_combo

            if combo:
                for i in range(combo.count()):
                    data = combo.itemData(i)
                    if isinstance(data, tuple) and data[0] == group_id:
                        combo.setCurrentIndex(i)
                        break

    def get_selected_group_info(self, entry_type):
        """获取当前选中的分组信息

        Returns:
            (group_id, group_name) 或 (None, None)
        """
        combo = None
        if entry_type == "discourse":
            combo = self.discourse_tab.group_combo
        elif entry_type == "dialogue":
            combo = self.dialogue_tab.group_combo

        if not combo or combo.currentIndex() <= 0:
            return None, None

        data = combo.currentData()
        if isinstance(data, tuple) and len(data) == 2:
            return data[0], data[1]

        return None, None

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

    def create_stats_tab(self):
        """创建统计标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.stats_layout = QVBoxLayout()
        scroll_content.setLayout(self.stats_layout)

        # === 语料概览 ===
        overview_group = QGroupBox("语料概览")
        overview_layout = QVBoxLayout()
        overview_group.setLayout(overview_layout)

        self.stats_total_label = QLabel("总计: 0 条")
        stats_font = self.stats_total_label.font()
        stats_font.setPointSize(16)
        stats_font.setBold(True)
        self.stats_total_label.setFont(stats_font)
        overview_layout.addWidget(self.stats_total_label)

        # 各类型进度条
        self.stats_type_bars = {}
        type_labels = {"word": "单词", "sentence": "单句", "discourse": "语篇", "dialogue": "对话"}
        for type_key, type_name in type_labels.items():
            row = QHBoxLayout()
            label = QLabel(f"{type_name}")
            label.setFixedWidth(40)
            row.addWidget(label)
            bar = QProgressBar()
            bar.setTextVisible(True)
            bar.setMinimum(0)
            bar.setMaximum(100)
            row.addWidget(bar)
            count_label = QLabel("0 (0%)")
            count_label.setFixedWidth(100)
            row.addWidget(count_label)
            self.stats_type_bars[type_key] = (bar, count_label)
            overview_layout.addLayout(row)

        self.stats_recent_label = QLabel("今日新增: 0条  本周: 0条")
        overview_layout.addWidget(self.stats_recent_label)

        self.stats_layout.addWidget(overview_group)

        # === 高频词汇 ===
        freq_group = QGroupBox("高频词汇 (Top 20)")
        self.freq_layout = QVBoxLayout()
        freq_group.setLayout(self.freq_layout)
        self.stats_layout.addWidget(freq_group)

        # === 标签分布 ===
        tags_group = QGroupBox("标签分布")
        self.tags_dist_layout = QVBoxLayout()
        tags_group.setLayout(self.tags_dist_layout)
        self.stats_layout.addWidget(tags_group)

        self.stats_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return widget

    def refresh_stats(self):
        """刷新统计面板"""
        stats = self.db.get_stats()
        total = stats['total']

        self.stats_total_label.setText(f"总计: {total:,} 条")

        for type_key, (bar, count_label) in self.stats_type_bars.items():
            count = stats['by_type'].get(type_key, 0)
            pct = round(count / total * 100) if total > 0 else 0
            bar.setValue(pct)
            bar.setFormat(f"{pct}%")
            count_label.setText(f"{count} ({pct}%)")

        self.stats_recent_label.setText(
            f"今日新增: {stats['today_count']}条  本周: {stats['week_count']}条"
        )

        # 高频词汇
        self._clear_layout(self.freq_layout)
        frequencies = self.db.get_word_frequencies(limit=20)
        if frequencies:
            max_freq = frequencies[0][1] if frequencies else 1
            for i, (word, count) in enumerate(frequencies, 1):
                row = QHBoxLayout()
                rank_label = QLabel(f"{i}.")
                rank_label.setFixedWidth(24)
                row.addWidget(rank_label)
                word_label = QLabel(word)
                word_label.setFixedWidth(120)
                word_label.setFont(_get_monospace_font(11))
                row.addWidget(word_label)
                bar = QProgressBar()
                bar.setMinimum(0)
                bar.setMaximum(max_freq)
                bar.setValue(count)
                bar.setFormat(f"{count}次")
                bar.setTextVisible(True)
                row.addWidget(bar)
                self.freq_layout.addLayout(row)
        else:
            self.freq_layout.addWidget(QLabel("暂无数据"))

        # 标签分布
        self._clear_layout(self.tags_dist_layout)
        tag_dist = self.db.get_tag_distribution()
        if tag_dist:
            max_count = tag_dist[0][1] if tag_dist else 1
            for tag, count in tag_dist:
                row = QHBoxLayout()
                tag_label = QLabel(tag)
                tag_label.setFixedWidth(80)
                row.addWidget(tag_label)
                bar = QProgressBar()
                bar.setMinimum(0)
                bar.setMaximum(max_count)
                bar.setValue(count)
                pct = round(count / total * 100) if total > 0 else 0
                bar.setFormat(f"{count} ({pct}%)")
                bar.setTextVisible(True)
                row.addWidget(bar)
                self.tags_dist_layout.addLayout(row)
        else:
            self.tags_dist_layout.addWidget(QLabel("暂无标签数据"))

    def _clear_layout(self, layout):
        """清空布局中的所有子项"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def add_entry(self):
        """添加语料"""
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

    def _validate_entry(self, tab: EntryTabWidget, current_id: int = None) -> list[str]:
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

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        new_db_action = QAction("新建数据库...", self)
        new_db_action.setShortcut("Ctrl+N")
        new_db_action.triggered.connect(self.new_database)
        file_menu.addAction(new_db_action)

        open_db_action = QAction("打开数据库...", self)
        open_db_action.setShortcut("Ctrl+O")
        open_db_action.triggered.connect(self.open_database)
        file_menu.addAction(open_db_action)

        save_as_action = QAction("另存为...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_database_as)
        file_menu.addAction(save_as_action)

        backup_action = QAction("备份数据库...", self)
        backup_action.triggered.connect(self.manual_backup)
        file_menu.addAction(backup_action)

        file_menu.addSeparator()

        print_action = QAction("打印...", self)
        print_action.setShortcut("Ctrl+P")
        print_action.triggered.connect(self.print_current_tab)
        file_menu.addAction(print_action)

        file_menu.addSeparator()

        quit_action = QAction("退出", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # 工具菜单
        tools_menu = menubar.addMenu("工具")

        dedup_action = QAction("去重检测...", self)
        dedup_action.setShortcut("Ctrl+D")
        dedup_action.triggered.connect(self.open_duplicate_detection)
        tools_menu.addAction(dedup_action)

        integrity_action = QAction("数据库完整性检查...", self)
        integrity_action.triggered.connect(self.check_database_integrity)
        tools_menu.addAction(integrity_action)

        tools_menu.addSeparator()

        ai_gloss_action = QAction("AI词汇分解分析...", self)
        ai_gloss_action.triggered.connect(self.ai_auto_gloss)
        tools_menu.addAction(ai_gloss_action)

        ai_translate_action = QAction("AI智能翻译...", self)
        ai_translate_action.triggered.connect(self.ai_auto_translate)
        tools_menu.addAction(ai_translate_action)

        # 设置菜单
        settings_menu = menubar.addMenu("设置")

        font_settings_action = QAction("字体设置...", self)
        font_settings_action.triggered.connect(self.open_font_settings)
        settings_menu.addAction(font_settings_action)

        toggle_theme_action = QAction("切换深色模式", self)
        toggle_theme_action.setShortcut("Ctrl+Shift+D")
        toggle_theme_action.triggered.connect(self.toggle_theme)
        settings_menu.addAction(toggle_theme_action)

        ai_settings_action = QAction("AI设置...", self)
        ai_settings_action.triggered.connect(self.open_ai_settings)
        settings_menu.addAction(ai_settings_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        about_action = QAction("关于 Fieldnotes Lite...", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

        shortcut_help_action = QAction("快捷键说明...", self)
        shortcut_help_action.triggered.connect(self.show_shortcut_help)
        help_menu.addAction(shortcut_help_action)

    def update_status_bar(self):
        """更新状态栏显示当前数据库"""
        db_path = self.db.db_path
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
            if not file_path.endswith('.db'):
                file_path += '.db'

            try:
                self.db.close()
                self.db = CorpusDatabase(file_path)
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
                self.db.close()
                self.db = CorpusDatabase(file_path)
                self.refresh_table()
                self.update_status_bar()
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
        current_db = self.db.db_path
        current_dir = os.path.dirname(current_db)
        current_name = os.path.basename(current_db)

        name_without_ext = os.path.splitext(current_name)[0]
        suggested_name = f"{name_without_ext}_副本.db"
        suggested_path = os.path.join(current_dir, suggested_name)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "数据库另存为",
            suggested_path,
            "数据库文件 (*.db);;所有文件 (*)"
        )

        if file_path:
            if not file_path.endswith('.db'):
                file_path += '.db'

            try:
                import shutil

                if os.path.exists(file_path):
                    reply = QMessageBox.question(
                        self,
                        "确认覆盖",
                        f"文件已存在：\n{file_path}\n\n是否覆盖？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply != QMessageBox.StandardButton.Yes:
                        return

                shutil.copy2(current_db, file_path)

                reply = QMessageBox.question(
                    self,
                    "另存为成功",
                    f"数据库已保存到：\n{file_path}\n\n是否切换到新数据库？\n"
                    f"(选择\"否\"将继续使用当前数据库)",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.db.close()
                    self.db = CorpusDatabase(file_path)
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

    def show_table_context_menu(self, pos):
        """显示表格右键菜单"""
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

    def export_selected_to_text(self, data_table, selected_rows):
        """导出选中的语料为文本"""
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
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
        except Exception as e:
            logger.error("加载字体配置失败: %s", e)

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
        source_font = self.font_config.get("source_text", "Doulos SIL Compact")
        source_size = self.font_config.get("source_text_size", 12)
        gloss_font = self.font_config.get("gloss", "Charis SIL Compact")
        gloss_size = self.font_config.get("gloss_size", 11)
        translation_font = self.font_config.get("translation", "系统默认")
        translation_size = self.font_config.get("translation_size", 11)
        chinese_font = self.font_config.get("chinese", "系统默认")
        chinese_size = self.font_config.get("chinese_size", 10)

        for tab in [self.word_tab, self.sentence_tab, self.discourse_tab, self.dialogue_tab]:
            if source_font != "系统默认":
                tab.source_text_input.setFont(QFont(source_font, source_size))
            if gloss_font != "系统默认":
                tab.gloss_input.setFont(QFont(gloss_font, gloss_size))
            if translation_font != "系统默认":
                tab.translation_input.setFont(QFont(translation_font, translation_size))
            if chinese_font != "系统默认":
                tab.source_text_cn_input.setFont(QFont(chinese_font, chinese_size))
                tab.gloss_cn_input.setFont(QFont(chinese_font, chinese_size))
                tab.translation_cn_input.setFont(QFont(chinese_font, chinese_size))

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
        shortcut_upper = QShortcut(QKeySequence("Ctrl+Shift+U"), self)
        shortcut_upper.activated.connect(lambda: self.transform_focused_text('upper'))

        shortcut_lower = QShortcut(QKeySequence("Ctrl+Shift+L"), self)
        shortcut_lower.activated.connect(lambda: self.transform_focused_text('lower'))

        shortcut_title = QShortcut(QKeySequence("Ctrl+Shift+T"), self)
        shortcut_title.activated.connect(lambda: self.transform_focused_text('title'))

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

        if text_edit.textCursor().hasSelection():
            menu.addSeparator()

            import platform
            modifier_key = "Cmd" if platform.system() == "Darwin" else "Ctrl"

            upper_action = QAction(f"转为大写 (NOM)\t{modifier_key}+Shift+U", self)
            upper_action.triggered.connect(lambda: self.transform_selected_text(text_edit, 'upper'))
            menu.addAction(upper_action)

            lower_action = QAction(f"转为小写 (nom)\t{modifier_key}+Shift+L", self)
            lower_action.triggered.connect(lambda: self.transform_selected_text(text_edit, 'lower'))
            menu.addAction(lower_action)

            title_action = QAction(f"首字母大写 (Nom)\t{modifier_key}+Shift+T", self)
            title_action.triggered.connect(lambda: self.transform_selected_text(text_edit, 'title'))
            menu.addAction(title_action)

            small_caps_action = QAction(f"小型大写 (ɴᴏᴍ)\t{modifier_key}+Shift+C", self)
            small_caps_action.triggered.connect(lambda: self.transform_selected_text(text_edit, 'small_caps'))
            menu.addAction(small_caps_action)

        menu.exec(text_edit.mapToGlobal(pos))

    def transform_focused_text(self, transform_type):
        """转换当前焦点输入框中选中的文本"""
        focused_widget = QApplication.focusWidget()
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
            transformed = self.to_small_caps(selected_text)
        else:
            return

        cursor.insertText(transformed)

    def to_small_caps(self, text):
        """将文本转换为Unicode小型大写字母"""
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

        return ''.join(small_caps_map.get(char, char) for char in text)

    # ===== 主题相关方法 =====

    def load_theme_preference(self) -> str:
        """从配置文件加载主题偏好"""
        config_path = os.path.join(os.path.expanduser("~"), ".fieldnote", "app_config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get("theme", "light")
        except Exception:
            pass
        return "light"

    def save_theme_preference(self):
        """保存主题偏好到配置文件"""
        config_path = os.path.join(os.path.expanduser("~"), ".fieldnote", "app_config.json")
        try:
            config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            config["theme"] = self.theme_manager.name
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("保存主题偏好失败: %s", e)

    def apply_theme(self):
        """应用当前主题到整个应用"""
        app = QApplication.instance()
        if app:
            app.setStyleSheet(self.theme_manager.generate_stylesheet())

    def toggle_theme(self):
        """切换深色/浅色主题"""
        new_theme = "dark" if self.theme_manager.name == "light" else "light"
        self.theme_manager.set_theme(new_theme)
        self.apply_theme()
        self.save_theme_preference()
        self.statusBar().showMessage(
            f"已切换到{'深色' if new_theme == 'dark' else '浅色'}模式", 3000
        )

    def _set_validation_style(self, label: QLabel, has_warning: bool):
        """根据主题设置验证标签样式"""
        c = self.theme_manager.colors
        if has_warning:
            label.setStyleSheet(
                f"padding: 4px; background: {c.warning_bg}; color: {c.warning_text}; "
                f"border: 1px solid {c.warning_border}; border-radius: 4px;"
            )
        else:
            label.setStyleSheet("padding: 4px;")

    # ===== 批量标签操作 =====

    def batch_tag_operation(self, data_table, selected_rows, mode: str):
        """批量标签操作入口"""
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

    # ===== CSV/JSON 导出 =====

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

    # ===== 搜索结果导出 =====

    def _get_search_result_entries(self) -> list:
        """获取搜索结果中的所有条目"""
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

    # ===== 去重检测 =====

    def open_duplicate_detection(self):
        """打开去重检测对话框"""
        dialog = DuplicateDetectionDialog(self, self.db, self.theme_manager)
        dialog.exec()
        self.refresh_table()

    # ===== 窗口状态记忆 =====

    def save_window_state(self):
        """保存窗口几何状态到配置文件"""
        config_path = os.path.join(os.path.expanduser("~"), ".fieldnote", "app_config.json")
        try:
            config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            geometry_bytes = self.saveGeometry()
            config["window_geometry"] = base64.b64encode(bytes(geometry_bytes)).decode('ascii')
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.debug("窗口状态已保存")
        except Exception as e:
            logger.error("保存窗口状态失败: %s", e)

    def restore_window_state(self):
        """从配置文件恢复窗口几何状态"""
        config_path = os.path.join(os.path.expanduser("~"), ".fieldnote", "app_config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                geometry_str = config.get("window_geometry")
                if geometry_str:
                    from PyQt6.QtCore import QByteArray
                    geometry_bytes = base64.b64decode(geometry_str)
                    self.restoreGeometry(QByteArray(geometry_bytes))
                    logger.debug("窗口状态已恢复")
        except Exception as e:
            logger.error("恢复窗口状态失败: %s", e)

    # ===== 备份与完整性检查 =====

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

    # ===== 打印功能 =====

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

    def show_about_dialog(self):
        """显示关于对话框"""
        dialog = AboutDialog(self)
        dialog.exec()

    def show_shortcut_help(self):
        """显示快捷键帮助对话框"""
        dialog = ShortcutHelpDialog(self)
        dialog.exec()

    # ===== AI 相关方法 =====

    def _init_ai_manager(self):
        """初始化 AI 管理器（失败不影响其他功能）"""
        try:
            from ai_backend import AIManager
            self.ai_manager = AIManager()
            logger.info("AI 管理器初始化成功")
        except Exception as e:
            logger.warning("AI 管理器初始化失败（AI 功能不可用）: %s", e)
            self.ai_manager = None

    def _ensure_ai_manager(self) -> bool:
        """确保 AI 可用，不可用则弹窗提示"""
        if self.ai_manager is None:
            QMessageBox.information(
                self, "AI 不可用",
                "AI 功能未初始化。请确认 ai_backend 模块存在。"
            )
            return False
        provider = self.ai_manager.get_provider()
        if provider is None:
            QMessageBox.information(
                self, "AI 未配置",
                "没有可用的 AI 提供者。\n\n"
                "请前往 设置 → AI设置 配置 Claude API 密钥或启动 Ollama 服务。"
            )
            return False
        return True

    def ai_auto_gloss(self):
        """AI 自动词汇分解"""
        if not self._ensure_ai_manager():
            return
        tab = self._get_current_tab()
        if tab is None:
            return

        source_text = tab.source_text_input.toPlainText().strip()
        if not source_text:
            QMessageBox.information(self, "提示", "请先输入原文再使用 AI 分析。")
            return

        source_text_cn = tab.source_text_cn_input.toPlainText().strip()

        # 获取 few-shot 上下文
        context_limit = self.ai_manager.config.max_context_entries
        context_entries = self.db.get_context_entries_for_gloss(limit=context_limit)

        # 构建 prompt
        from ai_prompts import build_gloss_prompt
        system_prompt, user_prompt = build_gloss_prompt(
            source_text, context_entries, source_text_cn
        )

        # 禁用按钮，显示"分析中..."
        tab.ai_gloss_btn.setEnabled(False)
        tab.ai_gloss_btn.setText("分析中")
        self.statusBar().showMessage("AI 词汇分解分析中...")

        # 创建工作线程
        from ai_widgets import AIWorkerThread
        self._ai_worker = AIWorkerThread(self.ai_manager, system_prompt, user_prompt, self)
        self._ai_worker.finished_signal.connect(
            lambda resp: self._on_ai_gloss_result(resp, tab)
        )
        self._ai_worker.start()

    def _on_ai_gloss_result(self, response, tab):
        """AI 词汇分解结果回调"""
        # 恢复按钮
        tab.ai_gloss_btn.setEnabled(True)
        tab.ai_gloss_btn.setText("AI分析")

        if response.success:
            existing = tab.gloss_input.toPlainText().strip()
            if existing:
                reply = QMessageBox.question(
                    self, "替换确认",
                    "词汇分解字段已有内容，是否替换为 AI 结果？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    self.statusBar().showMessage("已取消 AI 词汇分解替换")
                    return
            tab.gloss_input.setPlainText(response.text)
            self.statusBar().showMessage(
                f"AI 词汇分解完成（{response.provider_used}，"
                f"输入 {response.tokens_input} / 输出 {response.tokens_output} tokens）"
            )
        else:
            QMessageBox.warning(self, "AI 分析失败", response.error)
            self.statusBar().showMessage("AI 词汇分解失败")

    def ai_auto_translate(self):
        """AI 自动翻译"""
        if not self._ensure_ai_manager():
            return
        tab = self._get_current_tab()
        if tab is None:
            return

        source_text = tab.source_text_input.toPlainText().strip()
        if not source_text:
            QMessageBox.information(self, "提示", "请先输入原文再使用 AI 翻译。")
            return

        source_text_cn = tab.source_text_cn_input.toPlainText().strip()
        gloss = tab.gloss_input.toPlainText().strip()

        # 获取 few-shot 上下文
        context_limit = self.ai_manager.config.max_context_entries
        context_entries = self.db.get_context_entries_for_gloss(limit=context_limit)

        # 构建 prompt
        from ai_prompts import build_translation_prompt
        system_prompt, user_prompt = build_translation_prompt(
            source_text, gloss, context_entries, source_text_cn
        )

        # 禁用按钮，显示"翻译中..."
        tab.ai_translate_btn.setEnabled(False)
        tab.ai_translate_btn.setText("翻译中")
        self.statusBar().showMessage("AI 智能翻译中...")

        # 创建工作线程
        from ai_widgets import AIWorkerThread
        self._ai_worker = AIWorkerThread(self.ai_manager, system_prompt, user_prompt, self)
        self._ai_worker.finished_signal.connect(
            lambda resp: self._on_ai_translate_result(resp, tab)
        )
        self._ai_worker.start()

    def _on_ai_translate_result(self, response, tab):
        """AI 翻译结果回调"""
        # 恢复按钮
        tab.ai_translate_btn.setEnabled(True)
        tab.ai_translate_btn.setText("AI翻译")

        if response.success:
            existing = tab.translation_input.toPlainText().strip()
            if existing:
                reply = QMessageBox.question(
                    self, "替换确认",
                    "翻译字段已有内容，是否替换为 AI 结果？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    self.statusBar().showMessage("已取消 AI 翻译替换")
                    return
            tab.translation_input.setPlainText(response.text)
            self.statusBar().showMessage(
                f"AI 翻译完成（{response.provider_used}，"
                f"输入 {response.tokens_input} / 输出 {response.tokens_output} tokens）"
            )
        else:
            QMessageBox.warning(self, "AI 翻译失败", response.error)
            self.statusBar().showMessage("AI 翻译失败")

    def open_ai_settings(self):
        """打开 AI 设置对话框"""
        from ai_widgets import AISettingsDialog
        dialog = AISettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            config.save()
            if self.ai_manager:
                self.ai_manager.reload_config()
            else:
                self._init_ai_manager()
            self.statusBar().showMessage("AI 设置已保存")

    def closeEvent(self, event):
        """关闭事件处理"""
        self.save_window_state()
        self.db.close()
        event.accept()


class AboutDialog(QDialog):
    """关于对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于 Fieldnotes Lite")
        self.setFixedSize(420, 320)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        self.setLayout(layout)

        title = QLabel("Fieldnotes Lite")
        title_font = title.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        version = QLabel("版本 0.6.0")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        desc = QLabel("田野笔记管理与导出工具\n面向语言学田野调查的语料管理软件")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(8)

        info_text = (
            "著作权人: Linguistics Research\n"
            "开发日期: 2024-2026\n"
            "技术栈: Python + PyQt6 + SQLite\n"
        )
        info = QLabel(info_text)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        layout.addSpacing(8)

        copyright_label = QLabel("Copyright \u00a9 2024-2026 Linguistics Research.\nAll rights reserved.")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright_label)

        layout.addStretch()

        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)


class ShortcutHelpDialog(QDialog):
    """快捷键说明对话框"""

    SHORTCUTS = [
        ("Ctrl+N", "新建数据库"),
        ("Ctrl+O", "打开数据库"),
        ("Ctrl+Shift+S", "数据库另存为"),
        ("Ctrl+P", "打印当前语料"),
        ("Ctrl+Q", "退出程序"),
        ("Ctrl+D", "去重检测"),
        ("Ctrl+Shift+D", "切换深色模式"),
        ("Ctrl+Shift+U", "选中文本转大写"),
        ("Ctrl+Shift+L", "选中文本转小写"),
        ("Ctrl+Shift+T", "选中文本首字母大写"),
        ("Ctrl+Shift+C", "选中文本转小型大写"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("快捷键说明")
        self.setMinimumSize(400, 380)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["快捷键", "功能"])
        table.setRowCount(len(self.SHORTCUTS))
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)

        for row, (key, desc) in enumerate(self.SHORTCUTS):
            table.setItem(row, 0, QTableWidgetItem(key))
            table.setItem(row, 1, QTableWidgetItem(desc))

        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table)

        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)


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

        info_label = QLabel(
            "为不同字段设置专用字体（如Doulos SIL Compact用于IPA符号）\n"
            "字体必须已安装在系统中才能生效"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        layout.addSpacing(10)

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
        combo.setEditable(True)

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


class BatchTagDialog(QDialog):
    """批量标签操作对话框"""

    def __init__(self, parent, mode: str = 'add'):
        super().__init__(parent)
        self.mode = mode
        self.setWindowTitle("批量添加标签" if mode == 'add' else "批量移除标签")
        self.setMinimumWidth(400)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        hint = "选择要添加的标签：" if self.mode == 'add' else "选择要移除的标签："
        layout.addWidget(QLabel(hint))

        self.tag_selector = TagSelectorWidget()
        layout.addWidget(self.tag_selector)

        button_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def get_tags(self) -> list:
        return self.tag_selector.get_tags()


class DuplicateDetectionDialog(QDialog):
    """语料去重检测对话框"""

    def __init__(self, parent, db, theme_manager):
        super().__init__(parent)
        self.db = db
        self.theme_manager = theme_manager
        self._groups = []
        self.setWindowTitle("去重检测")
        self.setMinimumSize(1000, 650)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 上方：控制区
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("匹配模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["完全相同", "相似>90%", "相似>80%"])
        control_layout.addWidget(self.mode_combo)

        detect_btn = QPushButton("开始检测")
        detect_btn.clicked.connect(self._run_detection)
        control_layout.addWidget(detect_btn)
        control_layout.addStretch()
        layout.addLayout(control_layout)

        # 主体：左右分栏
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：重复组列表
        self.group_list = QListWidget()
        self.group_list.currentRowChanged.connect(self._on_group_selected)
        splitter.addWidget(self.group_list)

        # 右侧
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_widget.setLayout(right_layout)

        # 组内条目表格
        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(7)
        self.detail_table.setHorizontalHeaderLabels(
            ["ID", "例句编号", "原文", "翻译", "标签", "创建时间", ""]
        )
        self.detail_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.detail_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.detail_table.setAlternatingRowColors(True)
        self.detail_table.itemSelectionChanged.connect(self._on_detail_selection_changed)
        right_layout.addWidget(self.detail_table)

        # 差异对比区
        diff_group = QGroupBox("差异对比（选择两条记录）")
        diff_layout = QVBoxLayout()
        diff_group.setLayout(diff_layout)
        self.diff_display = QTextEdit()
        self.diff_display.setReadOnly(True)
        self.diff_display.setFont(_get_monospace_font(10))
        self.diff_display.setMaximumHeight(180)
        diff_layout.addWidget(self.diff_display)
        right_layout.addWidget(diff_group)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter)

        # 底部按钮
        bottom_layout = QHBoxLayout()
        self.delete_btn = QPushButton("删除选中的重复条目")
        self.delete_btn.clicked.connect(self._delete_selected)
        bottom_layout.addWidget(self.delete_btn)
        bottom_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        bottom_layout.addWidget(close_btn)
        layout.addLayout(bottom_layout)

    def _run_detection(self):
        """执行检测"""
        mode_map = {"完全相同": 1.0, "相似>90%": 0.9, "相似>80%": 0.8}
        threshold = mode_map[self.mode_combo.currentText()]

        self._groups = self.db.find_duplicates(threshold)
        self.group_list.clear()
        self.detail_table.setRowCount(0)
        self.diff_display.clear()

        if not self._groups:
            self.group_list.addItem("未发现重复项")
            return

        for i, group in enumerate(self._groups):
            preview = (group[0].get('source_text') or '')[:30]
            item_text = f"组{i+1}: {preview}... ({len(group)}条)"
            self.group_list.addItem(item_text)

    def _on_group_selected(self, index):
        """选择重复组时显示组内条目"""
        if index < 0 or index >= len(self._groups):
            self.detail_table.setRowCount(0)
            return

        group = self._groups[index]
        self.detail_table.setRowCount(len(group))

        for row, entry in enumerate(group):
            self.detail_table.setItem(row, 0, QTableWidgetItem(str(entry.get('id', ''))))
            self.detail_table.setItem(row, 1, QTableWidgetItem(entry.get('example_id', '') or ''))
            self.detail_table.setItem(row, 2, QTableWidgetItem(entry.get('source_text', '') or ''))
            self.detail_table.setItem(row, 3, QTableWidgetItem(entry.get('translation', '') or ''))
            self.detail_table.setItem(row, 4, QTableWidgetItem(entry.get('tags', '') or ''))
            created_at = entry.get('created_at', '') or ''
            if created_at and 'T' in created_at:
                created_at = created_at[:16].replace('T', ' ')
            self.detail_table.setItem(row, 5, QTableWidgetItem(created_at))

        self.detail_table.resizeColumnsToContents()
        self.diff_display.clear()

    def _on_detail_selection_changed(self):
        """选中两条时自动显示差异"""
        selected = self.detail_table.selectionModel().selectedRows()
        if len(selected) != 2:
            self.diff_display.clear()
            if len(selected) > 2:
                self.diff_display.setPlainText("请只选择两条记录来对比差异")
            return

        group_idx = self.group_list.currentRow()
        if group_idx < 0 or group_idx >= len(self._groups):
            return

        group = self._groups[group_idx]
        r1, r2 = selected[0].row(), selected[1].row()
        if r1 >= len(group) or r2 >= len(group):
            return

        entry_a, entry_b = group[r1], group[r2]

        lines = []
        compare_fields = [
            ('example_id', '例句编号'), ('source_text', '原文'),
            ('source_text_cn', '原文(汉字)'), ('gloss', '词汇分解'),
            ('gloss_cn', '词汇分解(汉字)'), ('translation', '翻译'),
            ('translation_cn', '翻译(汉字)'), ('notes', '备注'),
            ('tags', '标签'),
        ]

        for field, label in compare_fields:
            val_a = (entry_a.get(field) or '').strip()
            val_b = (entry_b.get(field) or '').strip()
            if val_a == val_b:
                lines.append(f"[=] {label}: {val_a}")
            else:
                lines.append(f"[!] {label}:")
                lines.append(f"    A (ID {entry_a.get('id')}): {val_a}")
                lines.append(f"    B (ID {entry_b.get('id')}): {val_b}")
                # unified diff for longer fields
                if len(val_a) > 20 or len(val_b) > 20:
                    diff = difflib.unified_diff(
                        val_a.splitlines(), val_b.splitlines(),
                        lineterm='', n=0
                    )
                    for d in diff:
                        if d.startswith(('---', '+++')):
                            continue
                        lines.append(f"    {d}")

        self.diff_display.setPlainText('\n'.join(lines))

    def _delete_selected(self):
        """删除选中的重复条目"""
        selected = self.detail_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的条目！")
            return

        count = len(selected)
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除选中的 {count} 条语料吗？\n\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            deleted = 0
            for index in selected:
                row = index.row()
                item = self.detail_table.item(row, 0)
                if item:
                    entry_id = int(item.text())
                    if self.db.delete_entry(entry_id):
                        deleted += 1

            QMessageBox.information(self, "删除成功", f"已删除 {deleted} 条语料！")
            # 重新检测
            self._run_detection()
