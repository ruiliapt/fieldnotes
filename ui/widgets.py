"""可复用组件模块 - IPAToolbarWidget, TagSelectorWidget, _get_monospace_font"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QCheckBox,
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont


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
