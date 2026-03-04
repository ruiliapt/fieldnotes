# Changelog

所有重要的项目更改都会记录在此文件中。

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

## [0.6.1] - 2026-03-04

### Added
- **OpenAI 兼容层**：新增 `OpenAICompatibleProvider`，统一接入 OpenAI / DeepSeek / 通义千问 / 智谱GLM / 百度文心
- AI 设置增强：预设下拉、Base URL、API Key、模型名称、测试连接
- 自动模式优先级：Claude → OpenAI Compatible → Ollama

## [0.6.0] - 2026-03-04

### Added
- **混合模式 AI 集成**：AI 后端抽象层 (`ai_backend.py`)、提示词模板 (`ai_prompts.py`)、界面组件 (`ai_widgets.py`)
- AI 词汇分解 + AI 智能翻译
- Few-shot 上下文自动查询
- 支持 Claude API 和 Ollama 本地模型

## [0.5.1] - 2026-03-04

### Added
- 日志系统 (`logger.py`)：RotatingFileHandler，30天自动清理
- 关于对话框、快捷键说明、帮助菜单
- 数据库自动备份 (`~/.fieldnote/backups/`) + 手动备份
- 数据库完整性检查 (PRAGMA integrity_check)
- 窗口状态记忆 (saveGeometry/restoreGeometry)
- 打印功能 (Ctrl+P)

## [0.5.0] - 2026-03-04

### Added
- 深色模式 (`theme.py`)：ThemeManager 全局 QSS，Ctrl+Shift+D 切换
- 批量标签管理：BatchTagDialog + batch_update_tags()
- CSV / JSON 导出，搜索结果一键导出
- 语料去重检测：DuplicateDetectionDialog（精确/模糊匹配）

## [0.4.0] - 2026-03-03

### Added
- IPA 音标工具栏（5分类：元音/辅音/声调/上标/变音符）
- 数据验证（词数不匹配警告、重复ID提示）
- 搜索高亮（匹配关键词背景高亮）
- 标签系统（TagSelectorWidget + 标签筛选）
- 统计面板（语料概览、高频词汇、标签分布）
- 时间戳（created_at/updated_at 自动记录）

### Changed
- 重构：EntryTabWidget 替代 property bag，提取公共方法消除重复
- database.py 统一 schema_version 迁移机制

## [0.3.0] - 2025-11-09

### Added
- 右键菜单功能：编辑、删除、导出、复制
- 字体设置增强：新增中文字体选项

### Changed
- Word 导出完全重构：动态换行、交错布局、单元格优化

## [0.2.0] - 2025-11-02

### Added
- 四种数据类型支持：单词/单句/语篇/对话
- 汉字字段支持、字体配置系统
- Word 导出优化：智能自动换行、紧凑表格
- 批量导入功能（JSON/CSV）
- GitHub Actions 自动化构建

## [0.1.4] - 2025-11-01

### Fixed
- **关键修复**: 排除导致崩溃的 Qt 权限插件
  - 移除 `qdarwinpermissionplugin_location` 插件避免全局初始化崩溃
  - 修改 PyInstaller spec 文件自定义打包配置
  - **真正解决** macOS 启动崩溃问题

## [0.1.3] - 2025-11-01

### Fixed
- **构建脚本完善**: 完全解决 macOS 启动崩溃问题
  - 确认移除 `--collect-all=PyQt6` 避免符号链接冲突
  - 优化 PyInstaller 配置确保稳定构建
  - 测试验证 .app 可正常启动

## [0.1.2] - 2025-11-01

### Fixed
- **构建脚本修复**: 更新 PyInstaller 配置避免符号链接冲突
  - 移除 `--collect-all=PyQt6` 标志（导致符号链接冲突）
  - 保留 `--copy-metadata` 确保 Qt 元数据正确打包
  - 构建过程更稳定可靠

## [0.1.1] - 2025-11-01

### Fixed
- **关键修复**: 解决 macOS 上启动立即崩溃的问题
  - 修复 QtCore 无法找到插件路径导致的 SIGSEGV 崩溃
  - 在导入 PyQt6 之前设置必要的环境变量
  - 添加 `--copy-metadata` 确保 Qt 元数据被正确打包
- 改进 PyInstaller 构建配置

### Added
- 崩溃诊断工具 (`scripts/debug_crash.sh`)
- 修复版构建脚本 (`scripts/build_executable_fixed.sh`)
- 完整的故障排除文档 (`docs/TROUBLESHOOTING.md`)
  - 8个常见问题的详细解决方案
  - macOS 安全提示处理
  - 路径和字体问题说明
- Qt 路径配置辅助模块 (`qt_conf_fix.py`)

### Changed
- 项目名称从 lite-corpus-manager 更新为 fieldnote
- 优化句号处理：原文末尾的单独句号自动合并到最后一个词

## [0.1.0] - 2025-10-19

### Added
- 初始版本发布
- 数据录入和管理功能（增删改查）
- 支持5个字段：例句编号、原文、词汇分解、翻译、备注
- 全文检索功能，支持字段搜索
- Word文档导出功能（三行对照表格格式）
- 批量导入功能（JSON/CSV格式）
- 支持Unicode和IPA字符
- 词对词对齐导出
- 透明表格样式
- 可自定义导出参数（表格宽度、字体大小、行距等）
- SQLite本地数据库存储
- PyQt6图形界面
- 跨平台支持（macOS/Linux/Windows）

### Documentation
- 完整的README文档
- 快速开始指南（QUICKSTART.md）
- 详细安装说明（INSTALL.md）
- 项目概览（PROJECT_OVERVIEW.md）
- 导出格式指南（EXPORT_FORMAT_GUIDE.md）
- 对齐技巧（ALIGNMENT_TIPS.md）

---

## 版本说明

### 版本号格式: MAJOR.MINOR.PATCH

- **MAJOR (主版本号)**: 不兼容的API修改
- **MINOR (次版本号)**: 向下兼容的功能性新增
- **PATCH (修订号)**: 向下兼容的问题修正

### 更新日志分类

- **Added**: 新增功能
- **Changed**: 功能变更
- **Deprecated**: 即将废弃的功能
- **Removed**: 已移除的功能
- **Fixed**: 错误修复
- **Security**: 安全性更新

