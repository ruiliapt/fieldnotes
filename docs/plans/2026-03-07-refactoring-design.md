# Fieldnotes Lite 全面重构设计

## 策略

**测试先行 (Test-First)**：先为现有代码建立完整测试套件，再在测试保护下逐步重构。

## 第一阶段：测试套件建设

为现有代码建立 pytest + pytest-qt 测试套件，作为重构安全网。

### 测试结构

```
tests/
  conftest.py              # 共享 fixtures（临时数据库、mock AI provider 等）
  test_database.py         # 数据库 CRUD、迁移、搜索、去重、备份
  test_exporter.py         # 文本对齐、Word 导出、字符宽度计算
  test_ai_backend.py       # 多 Provider 策略、配置持久化、错误处理
  test_ai_prompts.py       # Prompt 构建、few-shot 格式化
  test_theme.py            # 主题切换、样式表生成
  test_logger.py           # 日志轮转、清理
  test_gui/
    conftest.py            # pytest-qt fixtures
    test_main_window.py    # 窗口创建、菜单、状态栏
    test_tabs.py           # Tab 切换、数据录入
    test_search.py         # 搜索功能
    test_export_ui.py      # 导出 UI 交互
    test_ai_widgets.py     # AI 设置对话框
```

覆盖优先级：database > exporter > ai_backend > gui

## 第二阶段：gui.py 拆分为 ui/ 包

将 3,400 行的 MainWindow 拆分为职责清晰的模块，引入依赖注入。

### 目标结构

```
ui/
  __init__.py              # 导出 MainWindow
  main_window.py           # MainWindow 框架：菜单栏、状态栏、Tab 容器
  tab_manager.py           # 4 种数据 Tab 的创建和管理
  entry_tab_widget.py      # 单个数据录入 Tab 的控件
  data_operations.py       # CRUD 操作，统一 add/update 逻辑
  search_manager.py        # 搜索/过滤逻辑、搜索结果表格
  export_manager.py        # 协调所有导出操作（Text/Word/CSV/JSON）
  ai_coordinator.py        # AI 词汇分解和翻译的 UI 协调
  dialogs.py               # 共用对话框（关于、帮助、备份等）
  widgets.py               # 自定义可复用控件（IPA 工具栏等）
```

### 依赖注入

```python
class MainWindow(QMainWindow):
    def __init__(self, db: CorpusDatabase, exporter: WordExporter,
                 ai_manager: AIManager, theme: ThemeManager):
        ...
```

### 关键原则

- main_window.py 只做组装，不含业务逻辑
- 各模块通过 Qt 信号/槽通信，降低耦合
- data_operations.py 合并 add/update 重复逻辑
- 保持对外接口不变（main.py 调用方式只需微调）

## 第三阶段：其余模块优化

### API 密钥安全 — ai_backend.py

- 引入 keyring 依赖
- API key 存入系统密钥管理器，JSON 配置仅保留非敏感项
- 向后兼容：首次启动检测到旧明文 key 时自动迁移到 keyring，然后删除明文

### 数据库性能 — database.py

- 为 source_text、gloss、translation、tags、data_type 添加索引
- find_duplicates() 改用 SQL GROUP BY + HAVING COUNT > 1，O(n) 替代 O(n²)
- 关键操作加事务支持
- 新增 schema migration（SCHEMA_VERSION 3 → 4）

### exporter.py 优化

- 提取常量到类级别（字体大小、列宽、边距等）
- 拆分 export() 为 _validate()、_build_lines()、_create_table()、_fill_cells()
- 不改变外部接口

### 项目清理

- 删除过时脚本（build_executable_fixed.sh、冗余 run.bat/sh）
- 移除根目录测试产物 test_transparent_table_export.docx
- 添加 .editorconfig
