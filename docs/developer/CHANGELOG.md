# Changelog

所有重要的项目更改都会记录在此文件中。

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

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

