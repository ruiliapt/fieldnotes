# Fieldnotes Lite

田野笔记管理工具

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

### 方法1：使用 Poetry（推荐）

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

### JSON格式示例

```json
[
  {
    "example_id": "CJ001",
    "source_text": "ŋa˧ tə˥ tɕʰi˥ fan˨˩",
    "gloss": "1SG CLF eat rice",
    "translation": "我吃饭",
    "notes": "日常用语"
  },
  {
    "example_id": "CJ002",
    "source_text": "...",
    "gloss": "...",
    "translation": "...",
    "notes": ""
  }
]
```

### CSV格式示例

```csv
example_id,source_text,gloss,translation,notes
CJ001,"ŋa˧ tə˥ tɕʰi˥ fan˨˩","1SG CLF eat rice","我吃饭","日常用语"
CJ002,...,...,...,
```

## 数据库结构

使用SQLite数据库，表结构如下：

```sql
CREATE TABLE corpus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    example_id TEXT,
    source_text TEXT,
    gloss TEXT,
    translation TEXT,
    notes TEXT
);
```

数据库文件：`corpus.db`（自动创建在程序目录下）

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

- [跨平台打包指南](docs/developer/CROSS_PLATFORM_BUILD.md) ⭐ Windows/Linux/macOS 打包
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

