# Fieldnotes Lite

田野笔记管理工具

[![Build Release](https://github.com/ruiliapt/fieldnote/workflows/Build%20Release/badge.svg)](https://github.com/ruiliapt/fieldnote/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

---

> 💡 **给语言学研究者的提示**
> 
> 如果您**不熟悉编程**，请直接阅读：
> - **[一页纸快速指南](docs/user/ONE_PAGE_GUIDE.md)** ⭐ 5分钟上手
> - **[非技术用户使用指南](docs/user/USER_GUIDE_NON_TECHNICAL.md)** ⭐ 详细教程
> 
> 这两份文档用**最简单的语言**说明如何使用，不需要任何编程知识！

---

## 项目简介

Fieldnotes Lite 是一个面向语言学研究者的田野笔记管理工具，特别适用于田野调查数据、方言语料、少数民族语言记录等需要维护带音标和语法注释的语料。

### 主要功能

- ✅ **数据录入**：支持原文、词汇分解、翻译、备注等字段的输入
- ✅ **汉字注释**：支持为每个字段添加汉字注释（原文汉字、词汇分解汉字、翻译汉字）
- ✅ **数据分类**：支持单词、单句、语篇、对话四种数据类型
- ✅ **数据管理**：增删改查，支持Unicode和IPA字符
- ✅ **检索功能**：支持全文搜索和字段搜索
- ✅ **智能换行**：Word导出时根据内容宽度自动换行，无需手动设置
- ✅ **词对齐导出**：将语料导出为紧凑的词对词对齐表格（无边框、0边距）
- ✅ **汉字字段集成**：汉字注释直接嵌入表格，每个词垂直对齐
- ✅ **字体配置**：支持为各字段设置专业语言学字体（Doulos SIL、Charis SIL等）
- ✅ **小型大写**：支持Small Caps格式转换（用于语法标注）
- ✅ **批量导入**：支持JSON和CSV格式的批量导入
- ✅ **参数自定义**：可自定义表格宽度、字体大小、行距等导出参数

## 系统要求

### 支持的操作系统
- 🍎 **macOS** 10.15+ (Catalina 及更高版本)
- 🪟 **Windows** 10/11 (64位)
- 🐧 **Linux** (Ubuntu 20.04+, Debian 11+, Arch, Fedora 等)

### 依赖包
- Python 3.11+
- PyQt6
- python-docx
- pandas

> 详细的平台支持说明请查看 [跨平台支持文档](docs/developer/PLATFORM_SUPPORT.md)

## 安装

### 方法1：下载预编译版本 ⭐ 最简单

访问 [Releases 页面](https://github.com/ruiliapt/fieldnote/releases) 下载对应平台的安装包：

- 🪟 **Windows**: `Fieldnotes-Windows.zip` - 解压后直接运行 `Fieldnotes.exe`
- 🍎 **macOS**: `Fieldnotes-macOS.tar.gz` - 解压后双击 `Fieldnotes.app`
- 🐧 **Linux**: `Fieldnotes-Linux-x86_64.tar.gz` - 解压后运行 `./Fieldnotes`

> 💡 预编译版本无需安装 Python 和依赖，下载即用！

### 方法2：使用 Poetry（开发者）

1. 安装 Poetry（如果尚未安装）：
```bash
# macOS/Linux/WSL
curl -sSL https://install.python-poetry.org | python3 -

# Windows PowerShell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

2. 克隆或下载本项目：
```bash
git clone https://github.com/yourusername/fieldnote.git
cd fieldnote
```

3. 安装依赖：
```bash
poetry install
```

4. 运行程序：
```bash
poetry run python main.py
# 或直接使用
./scripts/run.sh    # macOS/Linux
scripts\run.bat     # Windows
```

### 方法2：使用传统方式

1. 克隆或下载本项目
2. 创建虚拟环境：
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate.bat  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

### 启动程序

**使用 Poetry：**
```bash
poetry run python main.py
# 或使用快捷方式
./scripts/run.sh    # macOS/Linux
scripts\run.bat     # Windows（双击或命令行运行）
```

**使用虚拟环境：**
```bash
source venv/bin/activate  # 先激活虚拟环境
python main.py
```

### 数据录入

1. 在"数据管理"标签页中填写语料信息：
   - **例句编号**：如 CJ001、TB002 等（可选）
   - **原文**：原始语料文本（支持IPA和Unicode）
   - **词汇分解**：形态学分析或注释
   - **翻译**：目标语言翻译
   - **备注**：附加说明（可选）

2. 点击"添加语料"保存

### 数据管理

- **编辑**：在表格中点击某行，数据会自动加载到输入框，修改后点击"更新语料"
- **删除**：选中某行后点击"删除语料"
- **批量导入**：准备JSON或CSV文件，点击"批量导入"

### 检索功能

1. 切换到"检索"标签页
2. 选择搜索字段（或选择"全部字段"）
3. 输入关键词
4. 点击"搜索"查看结果

### 导出Word文档

1. 切换到"导出"标签页
2. 设置导出参数：
   - 表格宽度（默认5英寸）
   - 字体大小（默认10pt）
   - 行距（默认1.15）
   - 是否显示编号
   - 每页语料数
3. 选择导出范围（全部或仅搜索结果）
4. 点击"导出到Word"并选择保存位置

### Word文档格式示例

导出的Word文档采用三行透明表格格式：

```
(CJ001)
┌────────────────────────────────┐
│ ŋa˧ tə˥ tɕʰi˥ fan˨˩            │  ← 原文
├────────────────────────────────┤
│ 1SG CLF eat rice               │  ← 词汇分解
├────────────────────────────────┤
│ 我吃饭                          │  ← 翻译
└────────────────────────────────┘
```

## 批量导入格式

Fieldnotes Lite 支持四种数据类型：**单词**、**单句**、**语篇**、**对话**。

### JSON格式示例

#### 单词 (word)
```json
[
  {
    "entry_type": "word",
    "example_id": "W001",
    "source_text": "ŋa˧",
    "gloss": "1SG",
    "translation": "我",
    "source_text_cn": "我",
    "gloss_cn": "第一人称单数",
    "translation_cn": "我",
    "notes": "人称代词"
  }
]
```

#### 单句 (sentence)
```json
[
  {
    "entry_type": "sentence",
    "example_id": "S001",
    "source_text": "ŋa˧ tə˥ tɕʰi˥ fan˨˩",
    "gloss": "1SG CLF eat rice",
    "translation": "我吃饭",
    "source_text_cn": "我吃饭",
    "gloss_cn": "我 量词 吃 饭",
    "translation_cn": "我吃饭",
    "notes": "日常用语"
  }
]
```

#### 语篇 (discourse)
```json
[
  {
    "entry_type": "discourse",
    "group_id": "D001",
    "group_name": "民间故事：猴子捞月",
    "example_id": "D001-01",
    "source_text": "jow˥˧ daw˥˧ gu˧˩",
    "gloss": "have INDEF monkey",
    "translation": "有一只猴子",
    "notes": "故事开头"
  },
  {
    "entry_type": "discourse",
    "group_id": "D001",
    "group_name": "民间故事：猴子捞月",
    "example_id": "D001-02",
    "source_text": "ta˧ kan˧˥ ta˧˥ te˧ ɲia˥",
    "gloss": "3SG see water inside moon",
    "translation": "它看到水里的月亮",
    "notes": "情节发展"
  }
]
```

#### 对话 (dialogue)
```json
[
  {
    "entry_type": "dialogue",
    "group_id": "C001",
    "group_name": "买菜对话",
    "speaker": "顾客",
    "turn_number": 1,
    "example_id": "C001-T01",
    "source_text": "tse˧ ko˧ to˥˧ ɕaw˧",
    "gloss": "this CLF how.much money",
    "translation": "这个多少钱？"
  },
  {
    "entry_type": "dialogue",
    "group_id": "C001",
    "group_name": "买菜对话",
    "speaker": "小贩",
    "turn_number": 2,
    "example_id": "C001-T02",
    "source_text": "wu˥ kway˥",
    "gloss": "five dollar",
    "translation": "五块钱"
  }
]
```

### CSV格式示例

```csv
entry_type,example_id,source_text,gloss,translation,source_text_cn,gloss_cn,translation_cn,notes,group_id,group_name,speaker,turn_number
sentence,S001,"ŋa˧ tə˥ tɕʰi˥ fan˨˩","1SG CLF eat rice","我吃饭","我吃饭","我 量词 吃 饭","我吃饭","日常用语",,,
word,W001,"ŋa˧","1SG","我","我","第一人称单数","我","人称代词",,,
discourse,D001-01,"jow˥˧ daw˥˧ gu˧˩","have INDEF monkey","有一只猴子",,,,"故事开头",D001,"民间故事：猴子捞月",,
dialogue,C001-T01,"tse˧ ko˧ to˥˧ ɕaw˧","this CLF how.much money","这个多少钱？",,,,D001,"买菜对话","顾客",1
```

### 字段说明

| 字段 | 必填 | 说明 | 适用类型 |
|------|------|------|----------|
| `entry_type` | 是 | 数据类型：word/sentence/discourse/dialogue | 全部 |
| `example_id` | 推荐 | 例句编号（如 S001） | 全部 |
| `source_text` | 是 | 原文（IPA或原始文字） | 全部 |
| `gloss` | 是 | 词汇分解/语法标注 | 全部 |
| `translation` | 是 | 翻译 | 全部 |
| `source_text_cn` | 否 | 原文汉字 | 全部 |
| `gloss_cn` | 否 | 词汇分解汉字 | 全部 |
| `translation_cn` | 否 | 翻译汉字 | 全部 |
| `notes` | 否 | 备注 | 全部 |
| `group_id` | 必填* | 语篇/对话组ID | discourse/dialogue |
| `group_name` | 推荐* | 语篇/对话组名称 | discourse/dialogue |
| `speaker` | 必填* | 说话人 | dialogue |
| `turn_number` | 推荐* | 对话轮次 | dialogue |

> **\*注**：语篇和对话类型必须填写 `group_id`，对话类型还必须填写 `speaker`

## 数据库结构

使用SQLite数据库，完整表结构如下：

```sql
CREATE TABLE corpus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    example_id TEXT,              -- 例句编号
    source_text TEXT,              -- 原文
    gloss TEXT,                    -- 词汇分解/语法标注
    translation TEXT,              -- 翻译
    notes TEXT,                    -- 备注
    source_text_cn TEXT,           -- 原文汉字
    gloss_cn TEXT,                 -- 词汇分解汉字
    translation_cn TEXT,           -- 翻译汉字
    entry_type TEXT DEFAULT 'sentence',  -- 数据类型: word/sentence/discourse/dialogue
    group_id TEXT,                 -- 语篇/对话组ID
    group_name TEXT,               -- 语篇/对话组名称
    speaker TEXT,                  -- 说话人（对话）
    turn_number INTEGER            -- 对话轮次
);
```

**数据库文件位置**：
- 默认：`~/.fieldnote/corpus.db`（用户主目录）
- 可通过"文件 > 另存为数据库"自定义位置

**数据类型说明**：
- `word`：单词条目
- `sentence`：单句条目（默认）
- `discourse`：语篇条目（需要 `group_id` 关联）
- `dialogue`：对话条目（需要 `group_id` 和 `speaker`）

## 技术架构

- **前端界面**：PyQt6
- **数据存储**：SQLite3
- **文档导出**：python-docx
- **编程语言**：Python 3.11+

## 项目结构

```
fieldnote/
├── main.py          # 主程序入口
├── gui.py           # 图形界面模块
├── database.py      # 数据库操作模块
├── exporter.py      # Word导出模块
├── requirements.txt # 依赖列表
├── README.md        # 项目说明
└── corpus.db        # SQLite数据库（运行后自动创建）
```

## 未来扩展

- [ ] LaTeX格式导出
- [ ] PDF直接导出
- [ ] 语料索引功能
- [ ] 云端同步
- [ ] 语义标注支持
- [ ] 多语言界面
- [ ] 音频关联

## 常见问题

### Q: 如何输入IPA字符？
A: 可以使用IPA输入法，或直接复制粘贴IPA字符。程序完全支持Unicode。

### Q: 数据存储在哪里？
A: 数据存储在程序目录下的 `corpus.db` SQLite数据库文件中，建议定期备份。

### Q: 如何备份数据？
A: 直接复制 `corpus.db` 文件即可。也可以导出为JSON格式备份。

### Q: 支持正则表达式搜索吗？
A: 当前版本支持模糊搜索（LIKE匹配），正则表达式支持将在后续版本中添加。

### Q: 可以同时打开多个程序窗口吗？
A: 不可以。Fieldnotes 使用单实例运行机制，防止数据库冲突。如果尝试再次启动，会提示"程序已在运行"。

### Q: 提示"程序已在运行"但找不到窗口怎么办？
A: 这可能是锁文件残留。运行 `./stop.sh`（macOS/Linux）或 `stop.bat`（Windows）清理后重新启动。详见 [单实例运行说明](SINGLE_INSTANCE.md)。

## 许可证

本项目采用 MIT 许可证。

## 贡献

欢迎提交问题报告和改进建议！

### 开发者文档

- [GitHub Actions 自动构建](docs/developer/GITHUB_ACTIONS_GUIDE.md) ⭐ 自动化跨平台打包
- [跨平台打包指南](docs/developer/CROSS_PLATFORM_BUILD.md) - Windows/Linux/macOS 手动打包
- [发布指南](docs/developer/PUBLISHING.md) - 如何发布新版本
- [快速发布](docs/developer/RELEASE_QUICKSTART.md) - 发布命令速查
- [项目概览](docs/developer/PROJECT_OVERVIEW.md) - 技术架构说明

## 面向不同用户的文档

### 🎓 语言学研究者（非技术用户）
- **[一页纸快速指南](docs/user/ONE_PAGE_GUIDE.md)** ⭐ 5分钟快速上手
- **[非技术用户使用指南](docs/user/USER_GUIDE_NON_TECHNICAL.md)** ⭐ 详细图文教程
- [快速开始](docs/developer/QUICKSTART.md) - 功能介绍

### 👨‍💻 技术用户/开发者
- [安装指南](docs/developer/INSTALL.md) - 详细安装说明
- [项目概览](docs/developer/PROJECT_OVERVIEW.md) - 技术架构
- [跨平台支持](docs/developer/PLATFORM_SUPPORT.md) - 平台兼容性
- [发布指南](docs/developer/PUBLISHING.md) - 如何发布软件

## 联系方式

如有问题或建议，请通过GitHub Issues联系。

---

**Fieldnotes Lite** - 让田野笔记管理更简单！

