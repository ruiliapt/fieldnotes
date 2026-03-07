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


from ui.widgets import IPAToolbarWidget, TagSelectorWidget, _get_monospace_font
from ui.entry_tab_widget import EntryTabWidget
from ui.data_operations import DataOperationsMixin
from ui.search_manager import SearchManagerMixin
from ui.export_manager import ExportManagerMixin
from ui.ai_coordinator import AICoordinatorMixin
from ui.dialogs import DialogsMixin


class MainWindow(QMainWindow, DataOperationsMixin, SearchManagerMixin,
                 ExportManagerMixin, AICoordinatorMixin, DialogsMixin):
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
        self.setWindowTitle("Fieldnotes Lite v0.6.1 - 田野笔记管理工具")
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
            'A': '\u1d00', 'B': '\u0299', 'C': '\u1d04', 'D': '\u1d05', 'E': '\u1d07', 'F': '\ua730', 'G': '\u0262', 'H': '\u029c',
            'I': '\u026a', 'J': '\u1d0a', 'K': '\u1d0b', 'L': '\u029f', 'M': '\u1d0d', 'N': '\u0274', 'O': '\u1d0f', 'P': '\u1d18',
            'Q': '\u01eb', 'R': '\u0280', 'S': '\ua731', 'T': '\u1d1b', 'U': '\u1d1c', 'V': '\u1d20', 'W': '\u1d21', 'X': 'x',
            'Y': '\u028f', 'Z': '\u1d22',
            'a': '\u1d00', 'b': '\u0299', 'c': '\u1d04', 'd': '\u1d05', 'e': '\u1d07', 'f': '\ua730', 'g': '\u0262', 'h': '\u029c',
            'i': '\u026a', 'j': '\u1d0a', 'k': '\u1d0b', 'l': '\u029f', 'm': '\u1d0d', 'n': '\u0274', 'o': '\u1d0f', 'p': '\u1d18',
            'q': '\u01eb', 'r': '\u0280', 's': '\ua731', 't': '\u1d1b', 'u': '\u1d1c', 'v': '\u1d20', 'w': '\u1d21', 'x': 'x',
            'y': '\u028f', 'z': '\u1d22'
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

        version = QLabel("版本 0.6.1")
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

        self.preview_label = QLabel("The quick brown fox jumps over the lazy dog\n\u0251 \u0254 \u0259 \u0283 \u0292 \u03b8 \u00f0 \u014b 测试汉字")
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
