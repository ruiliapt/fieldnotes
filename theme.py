"""
主题管理模块 - 深色/浅色主题切换
"""
from dataclasses import dataclass
from PyQt6.QtGui import QColor


@dataclass
class ThemeColors:
    """语义化颜色 token"""
    bg_primary: str
    bg_secondary: str
    bg_input: str
    bg_hover: str
    bg_selected: str
    bg_table_alt: str
    text_primary: str
    text_secondary: str
    text_muted: str
    border: str
    border_light: str
    accent: str
    accent_hover: str
    accent_text: str
    success: str
    warning_bg: str
    warning_text: str
    warning_border: str
    highlight: str


LIGHT_THEME = ThemeColors(
    bg_primary="#ffffff",
    bg_secondary="#f5f5f5",
    bg_input="#ffffff",
    bg_hover="#e0e0e0",
    bg_selected="#cce5ff",
    bg_table_alt="#f9f9f9",
    text_primary="#333333",
    text_secondary="#555555",
    text_muted="#666666",
    border="#cccccc",
    border_light="#dddddd",
    accent="#4CAF50",
    accent_hover="#45a049",
    accent_text="#ffffff",
    success="#4CAF50",
    warning_bg="#FFF3CD",
    warning_text="#856404",
    warning_border="#FFEEBA",
    highlight="#FFFF96",
)

DARK_THEME = ThemeColors(
    bg_primary="#1e1e1e",
    bg_secondary="#2d2d2d",
    bg_input="#3c3c3c",
    bg_hover="#4a4a4a",
    bg_selected="#264f78",
    bg_table_alt="#252525",
    text_primary="#d4d4d4",
    text_secondary="#aaaaaa",
    text_muted="#888888",
    border="#555555",
    border_light="#444444",
    accent="#4CAF50",
    accent_hover="#66BB6A",
    accent_text="#ffffff",
    success="#66BB6A",
    warning_bg="#4a3c00",
    warning_text="#ffcc02",
    warning_border="#665200",
    highlight="#5a5a00",
)


class ThemeManager:
    """主题管理器"""

    THEMES = {
        "light": LIGHT_THEME,
        "dark": DARK_THEME,
    }

    def __init__(self, theme_name: str = "light"):
        self._name = theme_name if theme_name in self.THEMES else "light"

    @property
    def name(self) -> str:
        return self._name

    @property
    def colors(self) -> ThemeColors:
        return self.THEMES[self._name]

    def set_theme(self, name: str):
        if name in self.THEMES:
            self._name = name

    def get_highlight_color(self) -> QColor:
        return QColor(self.colors.highlight)

    def generate_stylesheet(self) -> str:
        c = self.colors
        return f"""
        /* ===== 全局 ===== */
        QMainWindow, QDialog {{
            background-color: {c.bg_primary};
            color: {c.text_primary};
        }}
        QWidget {{
            color: {c.text_primary};
        }}

        /* ===== GroupBox ===== */
        QGroupBox {{
            border: 1px solid {c.border_light};
            border-radius: 4px;
            margin-top: 12px;
            padding-top: 14px;
            font-weight: bold;
            color: {c.text_primary};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px;
            color: {c.text_primary};
        }}

        /* ===== 输入控件 ===== */
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
            background-color: {c.bg_input};
            color: {c.text_primary};
            border: 1px solid {c.border};
            border-radius: 3px;
            padding: 3px;
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border-color: {c.accent};
        }}

        /* ===== ComboBox ===== */
        QComboBox {{
            background-color: {c.bg_input};
            color: {c.text_primary};
            border: 1px solid {c.border};
            border-radius: 3px;
            padding: 3px 6px;
        }}
        QComboBox::drop-down {{
            border: none;
        }}
        QComboBox QAbstractItemView {{
            background-color: {c.bg_input};
            color: {c.text_primary};
            selection-background-color: {c.bg_selected};
        }}

        /* ===== 按钮 ===== */
        QPushButton {{
            background-color: {c.bg_secondary};
            color: {c.text_primary};
            border: 1px solid {c.border};
            border-radius: 4px;
            padding: 5px 12px;
        }}
        QPushButton:hover {{
            background-color: {c.bg_hover};
        }}
        QPushButton:pressed {{
            background-color: {c.bg_selected};
        }}
        QPushButton[cssClass="accent"] {{
            background-color: {c.accent};
            color: {c.accent_text};
            border: 1px solid {c.accent};
            font-size: 14px;
            padding: 10px;
        }}
        QPushButton[cssClass="accent"]:hover {{
            background-color: {c.accent_hover};
        }}

        /* ===== 表格 ===== */
        QTableWidget {{
            background-color: {c.bg_primary};
            alternate-background-color: {c.bg_table_alt};
            color: {c.text_primary};
            gridline-color: {c.border_light};
            border: 1px solid {c.border_light};
            selection-background-color: {c.bg_selected};
        }}
        QHeaderView::section {{
            background-color: {c.bg_secondary};
            color: {c.text_primary};
            border: 1px solid {c.border_light};
            padding: 4px;
            font-weight: bold;
        }}

        /* ===== TabWidget ===== */
        QTabWidget::pane {{
            border: 1px solid {c.border_light};
            background-color: {c.bg_primary};
        }}
        QTabBar::tab {{
            background-color: {c.bg_secondary};
            color: {c.text_secondary};
            border: 1px solid {c.border_light};
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 6px 14px;
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{
            background-color: {c.bg_primary};
            color: {c.text_primary};
            border-bottom: 2px solid {c.accent};
        }}
        QTabBar::tab:hover:!selected {{
            background-color: {c.bg_hover};
        }}

        /* ===== 菜单栏 ===== */
        QMenuBar {{
            background-color: {c.bg_secondary};
            color: {c.text_primary};
            border-bottom: 1px solid {c.border_light};
        }}
        QMenuBar::item:selected {{
            background-color: {c.bg_hover};
        }}
        QMenu {{
            background-color: {c.bg_primary};
            color: {c.text_primary};
            border: 1px solid {c.border};
        }}
        QMenu::item:selected {{
            background-color: {c.bg_selected};
        }}
        QMenu::separator {{
            height: 1px;
            background: {c.border_light};
        }}

        /* ===== ScrollBar ===== */
        QScrollBar:vertical {{
            background: {c.bg_secondary};
            width: 12px;
            border: none;
        }}
        QScrollBar::handle:vertical {{
            background: {c.border};
            border-radius: 4px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {c.text_muted};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar:horizontal {{
            background: {c.bg_secondary};
            height: 12px;
            border: none;
        }}
        QScrollBar::handle:horizontal {{
            background: {c.border};
            border-radius: 4px;
            min-width: 20px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {c.text_muted};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}

        /* ===== ProgressBar ===== */
        QProgressBar {{
            background-color: {c.bg_secondary};
            border: 1px solid {c.border_light};
            border-radius: 4px;
            text-align: center;
            color: {c.text_primary};
        }}
        QProgressBar::chunk {{
            background-color: {c.accent};
            border-radius: 3px;
        }}

        /* ===== CheckBox ===== */
        QCheckBox {{
            color: {c.text_primary};
            spacing: 6px;
        }}
        QCheckBox::indicator {{
            width: 14px;
            height: 14px;
            border: 1px solid {c.border};
            border-radius: 2px;
            background-color: {c.bg_input};
        }}
        QCheckBox::indicator:checked {{
            background-color: {c.accent};
            border-color: {c.accent};
        }}

        /* ===== Label ===== */
        QLabel {{
            color: {c.text_primary};
        }}

        /* ===== StatusBar ===== */
        QStatusBar {{
            background-color: {c.bg_secondary};
            color: {c.text_secondary};
            border-top: 1px solid {c.border_light};
        }}

        /* ===== ScrollArea ===== */
        QScrollArea {{
            border: none;
            background-color: {c.bg_primary};
        }}

        /* ===== Frame ===== */
        QFrame {{
            color: {c.text_primary};
        }}
        """
