# Fieldnotes Lite - 项目结构

**最后更新**: 2026-03-07
**版本**: 0.7.0

---

## 目录结构

```
fieldnote/
├── docs/                           # 文档目录
│   ├── user/                       # 用户文档
│   │   ├── ONE_PAGE_GUIDE.md      # 一页纸快速指南
│   │   ├── USER_GUIDE_NON_TECHNICAL.md  # 非技术用户详细教程
│   │   └── README_DISTRIBUTION.md  # 分发指南
│   ├── developer/                  # 开发者文档
│   │   ├── QUICKSTART.md          # 快速开始
│   │   ├── INSTALL.md             # 安装指南
│   │   ├── PROJECT_OVERVIEW.md    # 项目概览
│   │   ├── PLATFORM_SUPPORT.md    # 跨平台支持
│   │   ├── PUBLISHING.md          # 发布指南
│   │   ├── BUILD_SUMMARY.md       # 构建总结
│   │   ├── SINGLE_INSTANCE.md     # 单实例运行说明
│   │   ├── RELEASE_QUICKSTART.md  # 发布快速参考
│   │   ├── CROSS_PLATFORM_BUILD.md    # 跨平台构建
│   │   └── GITHUB_ACTIONS_GUIDE.md    # CI/CD 指南
│   ├── guides/                     # 使用指南
│   │   ├── EXPORT_FORMAT_GUIDE.md # 导出格式指南
│   │   └── ALIGNMENT_TIPS.md      # 对齐技巧
│   ├── plans/                      # 设计/重构计划
│   ├── DOCS_INDEX.md              # 文档索引
│   └── README.md                  # 文档目录说明
│
├── ui/                             # GUI 模块包（v0.7.0 拆分自 gui.py）
│   ├── __init__.py                # 包导出
│   ├── main_window.py             # 主窗口 Mixin
│   ├── entry_tab_widget.py        # EntryTabWidget 条目标签页
│   ├── widgets.py                 # IPAToolbarWidget, TagSelectorWidget
│   ├── data_operations.py         # DataOperationsMixin (CRUD)
│   ├── search_manager.py          # SearchManagerMixin
│   ├── export_manager.py          # ExportManagerMixin
│   ├── ai_coordinator.py          # AICoordinatorMixin
│   ├── dialogs.py                 # DialogsMixin
│   └── tab_manager.py             # TabManager
│
├── tests/                          # 测试文件（pytest）
│   ├── conftest.py                # pytest fixtures
│   ├── test_database.py           # 数据库测试
│   ├── test_exporter.py           # 导出功能测试
│   ├── test_ai_backend.py         # AI 后端测试
│   ├── test_ai_prompts.py         # AI 提示词测试
│   ├── test_theme.py              # 主题测试
│   ├── test_logger.py             # 日志测试
│   └── test_gui/                  # GUI 组件测试
│       ├── conftest.py            # Qt fixtures
│       └── test_widgets.py        # Widget 测试
│
├── scripts/                        # 脚本目录
│   ├── build_executable.sh        # macOS/Linux 构建脚本
│   ├── build_executable.bat       # Windows 构建脚本
│   ├── release.sh                 # 发布脚本
│   ├── prepare_release.sh         # GitHub Release 准备脚本
│   ├── debug_crash.sh             # 崩溃诊断脚本
│   └── 启动Fieldnote.command       # macOS 双击启动脚本
│
├── samples/                        # 示例数据
│   ├── sample_data.json           # JSON 格式示例
│   ├── sample_data.csv            # CSV 格式示例
│   ├── sample_data_linguistic.json # 语言学数据示例
│   ├── sample_data_all_types.json # 全类型示例（JSON）
│   └── sample_data_all_types.csv  # 全类型示例（CSV）
│
├── hooks/                          # PyInstaller runtime hooks
│   └── rthook_qt_permissions.py   # Qt 权限修复
│
├── main.py                         # 程序入口（单实例检查）
├── gui.py                          # 图形界面主模块
├── database.py                     # 数据库模块（SQLite，Schema v4）
├── exporter.py                     # 导出模块（Word/CSV/JSON）
├── theme.py                        # 主题管理（深色/浅色模式）
├── ai_backend.py                   # AI 后端抽象层（多 LLM 支持）
├── ai_prompts.py                   # AI 提示词模板
├── ai_widgets.py                   # AI 界面组件
├── logger.py                       # 日志系统
├── qt_conf_fix.py                  # Qt 配置修复（打包用）
├── generate_copyright_docs.py      # 软著材料生成工具
│
├── README.md                       # 项目说明
├── CHANGELOG.md                    # 更新日志
├── LICENSE                         # MIT 许可证
├── pyproject.toml                  # Poetry 配置
├── Makefile                        # Make 任务
├── Fieldnotes.spec                 # PyInstaller 打包配置
├── .editorconfig                   # 编辑器配置
├── .gitignore                      # Git 忽略规则
└── PROJECT_STRUCTURE.md            # 本文件
```

---

## 主要文件说明

### 核心代码

| 文件 | 说明 | 依赖关系 |
|------|------|----------|
| `main.py` | 程序入口，单实例检查，启动 GUI | gui, logger |
| `gui.py` | 图形界面主模块，组合 ui/ 包中的 Mixin | database, exporter, theme, ai_widgets, ui/ |
| `database.py` | SQLite 封装，Schema 迁移（v4），索引优化 | 独立模块 |
| `exporter.py` | Word/CSV/JSON 导出 | python-docx |
| `theme.py` | 深色/浅色主题管理 | 独立模块 |
| `ai_backend.py` | AI 后端抽象层（Claude/OpenAI/Ollama） | 独立模块（urllib） |
| `ai_prompts.py` | 语言学专用 AI 提示词模板 | 独立模块 |
| `ai_widgets.py` | AI 设置对话框、工作线程 | ai_backend, ai_prompts |
| `logger.py` | 统一日志系统 | 独立模块 |

### ui/ 包

v0.7.0 从 gui.py 拆分，采用 Mixin 架构：

| 文件 | 说明 |
|------|------|
| `widgets.py` | IPAToolbarWidget, TagSelectorWidget |
| `entry_tab_widget.py` | EntryTabWidget 条目编辑标签页 |
| `data_operations.py` | DataOperationsMixin（增删改查） |
| `search_manager.py` | SearchManagerMixin（搜索功能） |
| `export_manager.py` | ExportManagerMixin（导出功能） |
| `ai_coordinator.py` | AICoordinatorMixin（AI 集成） |
| `dialogs.py` | DialogsMixin（对话框） |
| `tab_manager.py` | TabManager（标签页管理） |

---

## 常用命令

```bash
# 开发
make run          # 运行程序
make test         # 运行测试（pytest）
make clean        # 清理临时文件

# 构建
make build-exe    # 构建可执行文件

# 发布
make release      # 发布向导
make version      # 查看版本
```

详见 `Makefile`
