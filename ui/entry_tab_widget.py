"""条目标签页组件模块 - EntryTabWidget 类"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTextEdit, QTableWidget,
    QGroupBox, QFormLayout, QCheckBox, QComboBox, QApplication,
)
from PyQt6.QtCore import Qt

from ui.widgets import IPAToolbarWidget, TagSelectorWidget


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
