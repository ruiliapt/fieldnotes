# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.1] - 2026-03-04

### Added
- **OpenAI 兼容层**：新增 `OpenAICompatibleProvider`，统一接入所有 OpenAI `/v1/chat/completions` 兼容的 LLM 提供者
- **多 LLM 预设**：支持 OpenAI / DeepSeek / 通义千问 (Qwen) / 智谱GLM (Zhipu) / 百度文心 (ERNIE) / 自定义
- **AI 设置增强**：预设下拉选择、Base URL、API Key、模型名称配置、测试连接功能
- 自动模式优先级：Claude → OpenAI Compatible → Ollama

## [0.6.0] - 2026-03-04

### Added

#### 混合模式 AI 集成
- **AI 后端抽象层** (`ai_backend.py`)：Strategy 模式，支持 Claude / Ollama / Auto 三种模式
- **语言学专用 Prompt** (`ai_prompts.py`)：莱比锡标注规则 + few-shot 上下文模板
- **AI 工作线程** (`ai_widgets.py`)：QThread 异步处理 + AI 设置对话框
- **AI 词汇分解**：自动对语料进行词汇层面的分解分析，生成逐词注释
- **AI 智能翻译**：利用大语言模型进行高质量学术翻译
- **Few-shot 上下文**：自动查询已有语料作为 AI 参考上下文
- Ollama 零额外依赖（urllib.request），anthropic SDK 可选

## [0.5.1] - 2026-03-04

### Added
- **日志系统** (`logger.py`)：RotatingFileHandler，自动清理 30 天日志
- **关于对话框**：版本 / 版权 / 技术栈信息
- **快捷键说明**：列出全部 11 个快捷键
- **帮助菜单**：关于 + 快捷键说明
- **数据库自动备份**：每日启动静默备份到 `~/.fieldnote/backups/`
- **手动备份**：文件菜单 → 备份数据库
- **数据库完整性检查**：工具菜单 → PRAGMA integrity_check
- **窗口状态记忆**：saveGeometry / restoreGeometry via `app_config.json`
- **打印功能** (Ctrl+P)：QPrintDialog + QTextDocument HTML 表格

### Changed
- 全局 `print` 替换为 `logging` 模块

## [0.5.0] - 2026-03-04

### Added

#### 深色模式
- **ThemeManager** (`theme.py`)：深色 / 浅色主题切换，全局 QSS 覆盖
- 设置菜单快捷键 (Ctrl+Shift+D)，主题偏好持久化到 `app_config.json`
- 所有表格启用斑马纹 (alternatingRowColors)

#### 批量标签管理
- **BatchTagDialog**：批量添加 / 移除标签，支持右键菜单触发
- `database.py` 新增 `batch_update_tags()` 批量增删标签

#### 数据导出增强
- CSV 导出 (utf-8-sig BOM 兼容 Excel)
- JSON 导出 (ensure_ascii=False 支持中文)
- 搜索结果一键导出 CSV / JSON / Word

#### 语料去重
- **DuplicateDetectionDialog**：精确 / 模糊匹配 + 差异对比 + 删除
- `database.py` 新增 `find_duplicates()` (difflib.SequenceMatcher)

### Changed
- 移除 ~12 处 inline `setStyleSheet`，改为主题驱动

## [0.4.0] - 2026-03-03

### Added

#### IPA 音标工具栏
- 可折叠的 IPA 工具栏，5 个分类（元音 / 辅音 / 声调 / 上标 / 变音符）
- 点击符号即可插入到当前输入框

#### 数据验证
- 词数不匹配警告（不阻断保存）
- 重复 example_id 提示

#### 搜索高亮
- 匹配关键词的单元格背景高亮显示

#### 标签系统
- `TagSelectorWidget`：预设标签 + 自定义输入
- 搜索支持标签筛选

#### 统计面板
- 语料概览、高频词汇 Top20、标签分布

#### 时间戳
- 自动记录 `created_at` / `updated_at`
- 表格显示创建时间列

### Changed

#### 代码重构
- `EntryTabWidget` 替代 property bag 反模式
- 提取 `_get_monospace_font()` 消除 4 处重复
- 提取 `_show_text_export_dialog()` 消除 3 处重复
- `database.py` 统一 `schema_version` 迁移机制
- 修复 `datetime.utcnow()` 弃用警告

## [0.3.0] - 2025-11-09

### Added

#### 右键菜单功能 🖱️
- **语料列表右键菜单**：在语料列表中右键点击可快速执行操作
  - 编辑选中项：加载到表单进行编辑
  - 删除选中项：支持批量删除，带确认对话框
  - 导出为文本：将选中项导出为格式化文本
  - 导出为Word：将选中项导出为Word文档
  - 复制单元格内容：复制当前选中单元格的内容

#### 字体设置增强 🎨
- **新增中文字体选项**：宋体、Songti SC、SimSun、黑体、Heiti SC、SimHei、楷体、Kaiti SC、微软雅黑、Microsoft YaHei
- 更好地支持中文语料的字体显示

### Changed

#### Word导出完全重构 🚀

**动态换行策略**：
- ✅ 逐词检测是否会导致单元格压缩或超出页宽
- ✅ 基于字体大小动态计算页面可用宽度（15.9cm）
- ✅ 完全消除硬编码的每行词数限制
- ✅ 短词自动多放，长词自动少放

**交错布局**：
- ✅ 原文行和词汇分解行紧挨着（原文行1 → gloss行1 → 原文行2 → gloss行2）
- ✅ 更直观的词对词上下对应关系
- ✅ 汉字字段也跟随交错排列

**单元格优化**：
- ✅ 单元格内文本不换行（noWrap + keepLines）
- ✅ 左右边距统一为0.19cm
- ✅ 动态计算统一行高（基于所有词的最大高度）
- ✅ 表格占满页面宽度（100%）

**格式改进**：
- ✅ 移除翻译和翻译(汉字)的单引号包裹
- ✅ 统一单词和句子的导出逻辑

**完全动态化**：
- ✅ 行高基于字体大小和上标字符动态计算
- ✅ 页面宽度基于字体大小动态计算
- ✅ 校准系数随字体大小线性缩放
- ✅ 最小化硬编码值（仅保留物理尺寸：15.9cm、0.19cm）

### Technical

#### 核心算法
- `_estimate_word_height()`: 动态估算词的显示高度（考虑上标/下标）
- `_estimate_word_width()`: 动态估算词的显示宽度（考虑字符类型和边距）
- `_will_cause_overflow()`: 检测添加新词是否会导致压缩或溢出
- `_split_words_by_cumulative_width()`: 逐词累计宽度的动态分行算法

#### 代码改进
- `exporter.py`: 重构Word导出逻辑，实现交错布局和完全动态化
- `gui.py`: 添加右键菜单支持，新增多个菜单处理方法
- 移除所有硬编码的换行策略，改为基于数据的动态计算

## [0.2.0] - 2025-11-02

### Added

#### 数据类型系统 🗂️
- **四种数据类型支持**：单词（word）、单句（sentence）、语篇（discourse）、对话（dialogue）
- **语篇/对话分组管理**：通过 `group_id` 和 `group_name` 组织相关条目
- **说话人标记**：对话类型支持 `speaker` 和 `turn_number` 字段
- **数据分类界面**：独立的数据管理标签页，按类型查看和管理

#### 汉字字段支持 🇨🇳
- **三个汉字字段**：原文(汉字)、词汇分解(汉字)、翻译(汉字)
- **垂直对齐导出**：汉字词与对应的原文词在 Word 表格中垂直对齐
- **可选导出**：通过"包含汉字"选项控制是否导出汉字字段
- **录入界面优化**：字段按逻辑顺序排列（原文→原文汉字→词汇分解→词汇分解汉字→翻译→翻译汉字）

#### 字体配置系统 🔤
- **独立字体设置**：为原文、词汇分解、翻译、汉字字段分别配置字体
- **专业字体支持**：完美支持 Doulos SIL Compact、Charis SIL Compact 等语言学字体
- **Small Caps 转换**：右键菜单和上下文菜单支持小型大写转换
- **配置持久化**：字体设置自动保存和恢复

#### Word 导出优化 📄
- **智能自动换行**：根据内容宽度（中文2字符、英文1字符）自动分行，取代固定行数限制
- **紧凑表格布局**：一词一列，每列宽度自适应内容，无多余空白
- **智能垂直间距**：所有行（包括汉字行）使用一致的紧凑行高
- **字体映射**：导出时使用录入界面配置的字体
- **表格结构优化**：汉字字段完全集成到表格中，垂直对齐

#### 批量导入功能 📥
- **JSON 格式支持**：支持导入 JSON 格式的语料数据
- **CSV 格式支持**：支持导入 CSV 格式的语料数据
- **四种类型识别**：自动识别并正确导入不同类型的数据
- **示例数据**：提供完整的示例文件（`samples/sample_data_all_types.json` 和 `.csv`）

#### 自动化构建系统 🤖
- **GitHub Actions 集成**：自动跨平台构建（Windows、macOS、Linux）
- **测试构建工作流**：手动触发的测试构建，上传 artifacts
- **发布构建工作流**：推送标签时自动构建并创建 GitHub Release
- **依赖缓存**：Poetry 和 pip 缓存，加速构建过程

### Changed

#### 数据库结构
- 添加 `entry_type` 字段（默认 'sentence'）
- 添加 `group_id` 字段（语篇/对话组ID）
- 添加 `group_name` 字段（语篇/对话组名称）
- 添加 `speaker` 字段（说话人）
- 添加 `turn_number` 字段（对话轮次）
- 添加 `source_text_cn` 字段（原文汉字）
- 添加 `gloss_cn` 字段（词汇分解汉字）
- 添加 `translation_cn` 字段（翻译汉字）

#### 导出格式
- 编号与原文在同一行（之前编号单独一行）
- 汉字字段集成到表格中（之前在表格外）
- 移除固定的每行10词限制（现在智能换行）
- 统一紧凑的垂直间距（所有行高一致）

#### 界面优化
- 数据录入模块：分为"录入数据"和"已录入语料"两栏
- 数据管理模块：按数据类型分类显示
- 录入界面字段顺序：逻辑化排列，汉字字段紧随主字段
- "已录入语料"列表：显示所有字段（包括汉字字段）

### Fixed

#### macOS 打包问题
- 修复 Qt 权限插件导致的崩溃（排除 qdarwinpermission 等插件）
- 修复版本号显示为 0.0.0 的问题（添加 Info.plist 配置）
- 修复符号链接丢失问题（改用 tar.gz 代替 zip）

#### Windows 构建问题
- 修复 Poetry 在 GitHub Actions 中的安装问题
- 优化 Windows 构建脚本的依赖安装流程

#### 界面问题
- 修复数据录入后不显示在列表中的 bug
- 修复生成文本模块的编号对齐问题
- 修复 Word 导出表格的垂直间距问题

### Technical

#### 新增文件
- `Fieldnotes.spec` - PyInstaller 打包配置（替代 Fieldnote.spec）
- `hooks/rthook_qt_permissions.py` - Qt 权限插件运行时钩子
- `qt_conf_fix.py` - Qt 配置文件修复脚本
- `.github/workflows/test-build.yml` - 测试构建工作流
- `.github/workflows/build-release.yml` - 发布构建工作流
- `samples/sample_data_all_types.json` - 包含四种类型的示例数据
- `samples/sample_data_all_types.csv` - 包含四种类型的示例数据（CSV格式）

#### 代码重构
- `exporter.py`: 新增 `_split_words_by_width()` 方法（智能换行）
- `exporter.py`: 改进 `_set_cell_properties()` 方法（字体支持）
- `gui.py`: 重构数据录入模块（双栏布局）
- `gui.py`: 重构数据管理模块（按类型分类）
- `database.py`: 扩展数据库模式（新字段）

#### 文档完善
- 新增 `CHANGELOG.md` - 统一的变更日志
- 新增 `PROJECT_STRUCTURE.md` - 项目结构说明
- 新增 `docs/developer/GITHUB_ACTIONS_GUIDE.md` - GitHub Actions 使用指南
- 新增 `docs/developer/CROSS_PLATFORM_BUILD.md` - 跨平台打包指南
- 更新 `README.md` - 完整的功能说明和文档索引
- 新增 `docs/guides/ALIGNMENT_TIPS.md` - 对齐技巧
- 新增 `docs/guides/EXPORT_FORMAT_GUIDE.md` - 导出格式说明

## [0.1.4] - 2024-11-01

### Fixed
- 改进 macOS 打包流程
- 使用 tar.gz 格式保留符号链接

## [0.1.3] - 2024-11-01

### Fixed
- 修复 macOS 打包问题

## [0.1.2] - 2024-11-01

### Fixed
- 改进版本号管理

## [0.1.1] - 2024-11-01

### Fixed
- 修复发布流程

## [0.1.0] - 2024-11-01

### Added
- 初始版本发布
- 基础的语料录入功能
- Word 导出功能
- 数据库管理功能

---

**Note**: 详细的技术变更和代码级别的改动请参考 Git 提交历史。

