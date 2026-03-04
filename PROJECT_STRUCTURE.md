# Fieldnotes Lite - 项目结构

**最后更新**: 2026-03-04

---

## 📁 目录结构

```
fieldnote/
├── docs/                           # 📚 文档目录
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
│   │   ├── CHANGELOG.md           # 更新日志
│   │   ├── SINGLE_INSTANCE.md     # 单实例运行说明
│   │   ├── RELEASE_QUICKSTART.md  # 发布快速参考
│   │   ├── FINAL_SUCCESS.md       # 构建完成总结
│   │   ├── VERSION_0.1.0_FEATURES.md  # 版本功能清单
│   │   └── READY_TO_DISTRIBUTE.md # 分发就绪说明
│   ├── guides/                     # 使用指南
│   │   ├── EXPORT_FORMAT_GUIDE.md # 导出格式指南
│   │   └── ALIGNMENT_TIPS.md      # 对齐技巧
│   └── DOCS_INDEX.md              # 文档索引
│
├── scripts/                        # 🛠️ 脚本目录
│   ├── build_executable.sh        # macOS/Linux 构建脚本
│   ├── build_executable.bat       # Windows 构建脚本
│   ├── run.sh                     # macOS/Linux 运行脚本
│   ├── run.bat                    # Windows 运行脚本
│   ├── stop.sh                    # macOS/Linux 停止脚本
│   ├── stop.bat                   # Windows 停止脚本
│   ├── release.sh                 # 发布脚本
│   └── 启动Fieldnotes.command      # macOS 双击启动脚本
│
├── tests/                          # 🧪 测试文件
│   ├── test_basic.py              # 基础测试
│   ├── test_formatter.py          # 格式化测试
│   ├── test_long_multiline.py     # 多行测试
│   ├── test_long_sentence.py      # 长句测试
│   └── test_word_export.py        # 导出测试
│
├── samples/                        # 📋 示例数据
│   ├── sample_data.json           # JSON 格式示例
│   ├── sample_data_linguistic.json # 语言学数据示例
│   └── sample_data.csv            # CSV 格式示例
│
├── dist/                           # 📦 构建产物
│   ├── Fieldnotes.app              # macOS 应用程序（构建后）
│   ├── Fieldnotes/                 # 构建目录
│   ├── *.tar.gz                   # 分发压缩包（构建后）
│   ├── 使用说明.txt               # 用户说明文档
│   ├── ONE_PAGE_GUIDE.md          # 快速指南（分发用）
│   └── USER_GUIDE_NON_TECHNICAL.md # 详细教程（分发用）
│
├── main.py                         # 🚀 程序入口（单实例检查）
├── gui.py                          # 🖼️ 图形界面模块
├── database.py                     # 💾 数据库模块
├── exporter.py                     # 📄 导出模块（Word/CSV/JSON）
├── theme.py                        # 🎨 主题管理（深色/浅色模式）
├── ai_backend.py                   # 🤖 AI 后端抽象层（多 LLM 支持）
├── ai_prompts.py                   # 📝 AI 提示词模板
├── ai_widgets.py                   # 🧩 AI 界面组件
├── logger.py                       # 📋 日志系统
├── qt_conf_fix.py                  # 🔧 Qt 配置修复（打包用）
│
├── README.md                       # 项目说明
├── LICENSE                         # 许可证
├── pyproject.toml                  # Poetry 配置
├── requirements.txt                # pip 依赖清单
├── Makefile                        # Make 任务
├── .gitignore                      # Git 忽略规则
└── PROJECT_STRUCTURE.md            # 本文件（项目结构说明）
```

---

## 📄 主要文件说明

### 核心代码（根目录）

| 文件 | 说明 | 依赖关系 |
|------|------|----------|
| `main.py` | 程序入口，单实例检查，启动 GUI | 依赖 `gui.py`, `logger.py` |
| `gui.py` | 图形界面实现，主窗口逻辑 | 依赖 `database.py`, `exporter.py`, `theme.py`, `ai_widgets.py` |
| `database.py` | 数据库操作，SQLite 封装，迁移机制 | 独立模块 |
| `exporter.py` | 导出功能（Word/CSV/JSON） | 依赖 `python-docx` |
| `theme.py` | 深色/浅色主题管理 | 独立模块 |
| `ai_backend.py` | AI 后端抽象层，多 LLM 提供者 | 独立模块（urllib） |
| `ai_prompts.py` | 语言学专用 AI 提示词模板 | 独立模块 |
| `ai_widgets.py` | AI 设置对话框、工作线程 | 依赖 `ai_backend.py`, `ai_prompts.py` |
| `logger.py` | 统一日志系统 | 独立模块 |
| `qt_conf_fix.py` | Qt 配置文件修复（打包环境） | 独立模块 |

### 配置文件

| 文件 | 说明 |
|------|------|
| `pyproject.toml` | Poetry 项目配置，依赖管理 |
| `requirements.txt` | pip 依赖列表（从 Poetry 导出） |
| `Makefile` | 常用任务快捷命令 |
| `.gitignore` | Git 版本控制忽略规则 |

### 脚本文件（scripts/）

| 文件 | 平台 | 用途 |
|------|------|------|
| `run.sh` / `run.bat` | macOS/Linux / Windows | 快速启动程序 |
| `build_executable.sh` / `build_executable.bat` | macOS/Linux / Windows | 构建可执行文件 |
| `stop.sh` / `stop.bat` | macOS/Linux / Windows | 安全停止程序 |
| `release.sh` | macOS/Linux | 发布新版本向导 |
| `启动Fieldnotes.command` | macOS | 双击启动脚本 |

---

## 🗂️ 文档组织

### 用户文档（docs/user/）
面向**最终用户**（语言学研究者），不需要编程知识：
- `ONE_PAGE_GUIDE.md` - 5分钟快速上手
- `USER_GUIDE_NON_TECHNICAL.md` - 详细使用教程
- `README_DISTRIBUTION.md` - 如何分发给同事

### 开发者文档（docs/developer/）
面向**开发者和维护者**，需要技术背景：
- `QUICKSTART.md` - 开发环境快速搭建
- `INSTALL.md` - 详细安装步骤
- `PROJECT_OVERVIEW.md` - 架构设计说明
- `PLATFORM_SUPPORT.md` - 跨平台开发指南
- `PUBLISHING.md` - 发布流程说明
- `BUILD_SUMMARY.md` - 构建流程文档
- `CHANGELOG.md` - 版本更新历史
- `SINGLE_INSTANCE.md` - 单实例运行技术说明
- `RELEASE_QUICKSTART.md` - 发布命令快速参考

### 使用指南（docs/guides/）
面向**所有用户**，特定功能的深入说明：
- `EXPORT_FORMAT_GUIDE.md` - Word 导出格式详解
- `ALIGNMENT_TIPS.md` - 词对词对齐技巧

---

## 🛠️ 开发工作流

### 日常开发
```bash
# 1. 激活环境
poetry shell

# 2. 运行程序
python main.py
# 或
./scripts/run.sh

# 3. 运行测试
python tests/test_basic.py

# 4. 停止程序
./scripts/stop.sh
```

### 构建发布
```bash
# 1. 清理旧构建
make clean

# 2. 运行测试
python tests/test_basic.py

# 3. 构建可执行文件
./scripts/build_executable.sh

# 4. 测试可执行文件
open dist/Fieldnotes.app

# 5. 创建分发包
cd dist
tar -czf Fieldnotes-0.1.0-macOS.tar.gz Fieldnotes.app *.txt *.md
```

---

## 📦 构建产物（dist/）

构建后的 `dist/` 目录包含：

```
dist/
├── Fieldnotes.app/              # macOS 应用程序包
│   └── Contents/
│       ├── MacOS/
│       │   └── Fieldnotes       # 可执行文件
│       ├── Frameworks/         # 依赖库
│       ├── Resources/          # 资源文件
│       └── Info.plist          # 应用信息
│
├── Fieldnotes/                  # 打包目录（中间产物）
│
├── Fieldnotes-0.1.0-macOS-Complete.tar.gz  # 完整分发包
│
├── 使用说明.txt                 # 用户说明
├── ONE_PAGE_GUIDE.md           # 快速指南
└── USER_GUIDE_NON_TECHNICAL.md # 详细教程
```

---

## 🧪 测试文件（tests/）

| 文件 | 测试内容 |
|------|----------|
| `test_basic.py` | 数据库基础操作 |
| `test_formatter.py` | 格式化函数测试 |
| `test_word_export.py` | Word 导出功能 |
| `test_long_sentence.py` | 长句处理 |
| `test_long_multiline.py` | 多行文本处理 |

运行测试：
```bash
# 单个测试
python tests/test_basic.py

# 所有测试
python -m pytest tests/
```

---

## 📋 示例数据（samples/）

提供三种示例数据格式：

1. **sample_data.json** - 基础 JSON 格式
2. **sample_data_linguistic.json** - 语言学专业数据
3. **sample_data.csv** - CSV 表格格式

用途：
- 新用户学习数据格式
- 测试批量导入功能
- 演示程序功能

---

## 🔄 Git 工作流

### 分支策略
- `main` - 稳定版本
- `develop` - 开发分支
- `feature/*` - 功能分支

### 提交前检查
```bash
# 1. 检查代码
make lint

# 2. 运行测试
make test

# 3. 清理临时文件
make clean
```

---

## 📝 添加新功能的步骤

1. **编写代码**
   - 在根目录的 Python 文件中添加功能
   - 保持模块化设计

2. **编写测试**
   - 在 `tests/` 目录添加测试文件
   - 命名格式：`test_<feature>.py`

3. **更新文档**
   - 用户功能 → `docs/user/`
   - 技术说明 → `docs/developer/`
   - 使用技巧 → `docs/guides/`

4. **更新 README**
   - 添加功能描述
   - 更新使用说明

5. **更新 CHANGELOG**
   - 记录在 `docs/developer/CHANGELOG.md`

---

## 💡 项目设计原则

### 文件组织原则
1. **分离关注点** - 代码/文档/脚本/测试分开
2. **用户优先** - 用户文档独立且易找
3. **开发友好** - 脚本集中，易于维护
4. **构建隔离** - 构建产物与源码分离

### 命名规范
- **Python 文件** - 小写下划线：`database.py`
- **文档文件** - 大写下划线：`USER_GUIDE.md`
- **脚本文件** - 小写下划线：`build_executable.sh`
- **目录名** - 小写：`docs/`, `scripts/`, `tests/`

---

## 🎯 常用命令

```bash
# 开发
make run          # 运行程序
make test         # 运行测试
make clean        # 清理临时文件

# 构建
make build-exe    # 构建可执行文件

# 发布
make release      # 发布向导
make version      # 查看版本
```

详见 `Makefile`

---

**项目结构说明文档** - Fieldnotes Lite v0.6.1

