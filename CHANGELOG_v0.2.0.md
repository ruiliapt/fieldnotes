# Changelog v0.2.0 - Word导出功能重大升级

**发布日期**：2025-11-02

## 📋 本次更新总览

本次更新主要优化了 Word 导出功能，实现了智能换行、汉字字段对齐、字体配置等重要特性，使导出的文档更加专业和美观。

---

## ✨ 新增功能

### 1. 智能自动换行 🔄

**问题背景**：之前固定每行10个词，导致短词浪费空间，长词可能超宽。

**解决方案**：
- ✅ 移除固定的 `max_words_per_line = 10` 限制
- ✅ 根据实际显示宽度（字符数）自动分行
- ✅ 智能计算每个词的显示宽度（中文2字符，英文1字符）
- ✅ 设定最大行宽 80 字符，自动决定换行位置

**效果**：
```
之前：每行固定10个词，无论长短
现在：短词多放（可能15个），长词少放（可能5个）
```

**技术实现**：
- 新增 `_split_words_by_width()` 方法
- 使用 `TextFormatter.calculate_display_width()` 计算字符宽度
- 考虑词间空格（2字符）

---

### 2. 汉字字段完全集成到表格 📊

**问题背景**：汉字字段之前是表格外的独立段落，不够整洁。

**解决方案**：
- ✅ 原文(汉字)、词汇分解(汉字)集成到表格中
- ✅ 每个汉字词对应一个单元格，与主字段垂直对齐
- ✅ 翻译(汉字)合并显示在一行
- ✅ 通过"包含汉字"选项控制是否导出
- ✅ 移除字段标签，只显示内容

**表格结构**（选择"包含汉字"时）：
```
行1: (1)  word1   word2   word3   word4   ← 原文
行2: 空   汉字1   汉字2   汉字3   汉字4   ← 原文(汉字)，垂直对齐
行3: 空   gloss1  gloss2  gloss3  gloss4  ← 词汇分解
行4: 空   汉字1   汉字2   汉字3   汉字4   ← 词汇分解(汉字)，垂直对齐
行5: 空   'translation'                    ← 翻译（合并）
行6: 空   '汉字翻译'                       ← 翻译(汉字)（合并）
```

**垂直对齐效果**：
- 第1列：word1 → 汉字1 → gloss1 → 汉字1
- 第2列：word2 → 汉字2 → gloss2 → 汉字2
- 第3列：word3 → 汉字3 → gloss3 → 汉字3

**技术实现**：
- 汉字字段也进行分词处理
- 使用 `source_cn_lines_list` 和 `gloss_cn_lines_list` 存储分行结果
- 动态计算表格行数（包含汉字字段行）

---

### 3. 字体配置支持 🔤

**问题背景**：导出的字体与录入界面不一致。

**解决方案**：
- ✅ 导出时使用录入界面设置的字体
- ✅ 支持为各字段独立设置字体
- ✅ 完美支持语言学专业字体
- ✅ 字体配置自动保存和恢复

**字体映射关系**：
```
录入界面设置              →  Word导出使用
────────────────────────────────────────
原文字体                  →  原文内容、编号
  默认: Doulos SIL Compact, 12号

词汇分解字体              →  词汇分解内容
  默认: Charis SIL Compact, 11号

翻译字体                  →  翻译内容
  默认: 系统默认, 11号

汉字字段字体              →  所有汉字字段
  默认: 系统默认, 10号
```

**技术实现**：
- 在 `export()` 方法中添加 `font_config` 参数
- 在 `_set_cell_properties()` 中添加 `font_name` 参数
- GUI 调用 export 时传递 `self.font_config`
- 为每个单元格设置对应的字体名称和大小

---

## 🔧 代码优化

### 1. 新增辅助函数

**`_set_cell_properties(cell, font_size, is_content_cell, font_name)`**
- 统一设置单元格属性（宽度、对齐、边距、字体）
- 避免重复代码，提高可维护性
- 代码量从 ~200行 减少到 ~60行

**`_split_words_by_width(words, max_width)`**
- 根据显示宽度智能分行
- 支持中英文混合计算
- 考虑词间空格

### 2. 参数结构改进

**之前**：
```python
def export(entries, output_path, font_size=10, ...)
```

**现在**：
```python
def export(entries, output_path, font_size=10, 
           font_config={...}, ...)
```

### 3. 行数计算动态化

```python
# 计算总行数：原文 + 原文(汉字) + gloss + gloss(汉字) + 翻译 + 翻译(汉字)
total_rows = source_line_count + gloss_line_count + 1
if include_chinese:
    if source_words_cn:
        total_rows += len(source_cn_lines_list)
    if gloss_words_cn:
        total_rows += len(gloss_cn_lines_list)
    if translation_cn:
        total_rows += 1
```

---

## 📝 文件修改清单

### 修改的文件

1. **exporter.py** (+156 lines, -108 lines)
   - 新增 `_split_words_by_width()` 方法
   - 修改 `_set_cell_properties()` 添加字体支持
   - 重构表格填充逻辑，支持汉字字段对齐
   - 添加 `font_config` 参数

2. **gui.py** (+3 lines, -3 lines)
   - 在所有 `export()` 调用处传递 `font_config`

3. **README.md** (+10 lines, -4 lines)
   - 更新主要功能列表
   - 添加新功能说明

---

## 🎯 使用说明

### 智能换行

无需任何配置，系统会自动根据内容宽度换行。

**示例**：
- 15个短英文词 → 可能2-3行
- 5个长中文短语 → 可能3-4行
- 中英混合 → 智能计算

### 汉字字段对齐

**录入时**：
```
原文：word1 word2 word3
原文(汉字)：汉字1 汉字2 汉字3  ← 用空格分隔，与原文对应
```

**导出效果**：
- 每列垂直对齐
- word1 下方是 汉字1
- word2 下方是 汉字2
- word3 下方是 汉字3

### 字体配置

1. 打开"设置" → "字体设置"
2. 为每个字段选择字体和大小
3. 导出时会自动使用这些设置

**推荐字体**：
- 原文：Doulos SIL Compact（国际音标）
- 词汇分解：Charis SIL Compact（语法标注）
- 翻译：系统默认
- 汉字：系统默认

---

## 🐛 已知问题

无

---

## 📦 兼容性

- ✅ 向后兼容：旧版本的数据库可以直接使用
- ✅ 导出格式：生成标准的 .docx 文件
- ✅ 平台支持：macOS、Windows、Linux

---

## 🙏 致谢

感谢用户反馈和测试！

---

## 🔜 后续计划

- [ ] 支持批量编辑
- [ ] 支持导出为 PDF
- [ ] 支持自定义导出模板
- [ ] 支持音频关联

---

**Commit**: f227250
**Branch**: main

