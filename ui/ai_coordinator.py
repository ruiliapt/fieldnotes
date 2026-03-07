"""AI 协调混入 - AICoordinatorMixin"""
import logging

from PyQt6.QtWidgets import QMessageBox, QDialog

logger = logging.getLogger(__name__)


class AICoordinatorMixin:
    """Mixin for AI-related operations (gloss, translate, settings)."""

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
