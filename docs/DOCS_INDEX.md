# Fieldnotes Lite - 文档索引

本项目提供了完整的文档，面向不同类型的用户。

---

## 📚 文档结构

```
fieldnote/
├── 📖 面向所有用户
│   ├── README.md                          # 项目首页，总览
│   └── LICENSE                            # MIT 开源协议
│
├── 🎓 面向语言学家（非技术用户）⭐
│   ├── ONE_PAGE_GUIDE.md                  # ⭐⭐⭐ 一页纸快速指南（5分钟）
│   ├── USER_GUIDE_NON_TECHNICAL.md        # ⭐⭐⭐ 详细使用教程（零基础）
│   └── QUICKSTART.md                      # 快速开始指南
│
├── 👨‍💻 面向技术用户/开发者
│   ├── INSTALL.md                         # 详细安装说明
│   ├── PROJECT_OVERVIEW.md                # 项目技术概览
│   ├── PLATFORM_SUPPORT.md                # 跨平台支持说明
│   ├── SINGLE_INSTANCE.md                 # 单实例运行说明
│   ├── ALIGNMENT_TIPS.md                  # 对齐技巧
│   └── EXPORT_FORMAT_GUIDE.md             # 导出格式指南
│
├── 🚀 面向发布者/维护者
│   ├── PUBLISHING.md                      # 完整发布指南
│   ├── RELEASE_QUICKSTART.md              # 发布命令速查
│   └── README_DISTRIBUTION.md             # 面向非技术用户的分发建议
│
└── 📦 示例数据
    ├── sample_data.json                   # JSON 格式示例
    ├── sample_data.csv                    # CSV 格式示例
    └── sample_data_linguistic.json        # 语言学数据示例
```

---

## 🎯 我是什么样的用户？

### 👤 语言学研究者（不懂编程）

**您需要的文档**：

1. **[一页纸快速指南](ONE_PAGE_GUIDE.md)** ⭐⭐⭐
   - 📄 1页，5分钟读完
   - 🎯 最基本的使用方法
   - 📥 如何获取软件
   - 💾 如何备份数据

2. **[非技术用户使用指南](USER_GUIDE_NON_TECHNICAL.md)** ⭐⭐⭐
   - 📄 长文，详细教程
   - 🎯 零基础入门
   - 📸 图解界面（推荐添加截图）
   - ❓ 常见问题解答

3. **[快速开始](QUICKSTART.md)**
   - 📄 功能介绍
   - 🎯 了解能做什么

**您不需要看**：
- ❌ 任何包含"Python"、"Poetry"、"Git"的文档
- ❌ 技术架构、发布流程等

---

### 👨‍🏫 实验室管理员/IT 支持

**您需要的文档**：

1. **[安装指南](INSTALL.md)**
   - 帮助用户安装

2. **[面向非技术用户的分发建议](README_DISTRIBUTION.md)** ⭐
   - 📦 如何制作安装包
   - 🎓 如何组织培训
   - 🆘 如何提供技术支持

3. **[跨平台支持说明](PLATFORM_SUPPORT.md)**
   - 不同系统的注意事项
   - 故障排除

---

### 👨‍💻 有 Python 经验的用户

**您需要的文档**：

1. **[安装指南](INSTALL.md)** ⭐
   - Poetry 安装方法
   - 传统安装方法

2. **[快速开始](QUICKSTART.md)**
   - 功能概览

3. **[项目概览](PROJECT_OVERVIEW.md)**
   - 技术架构
   - 代码结构

---

### 🛠️ 开发者/贡献者

**您需要的文档**：

1. **[项目概览](PROJECT_OVERVIEW.md)** ⭐
   - 📊 技术架构
   - 🏗️ 项目结构
   - 🧪 测试方法

2. **[跨平台支持说明](PLATFORM_SUPPORT.md)**
   - 🌍 平台兼容性
   - 🐛 平台特定问题

3. **[发布指南](PUBLISHING.md)**（如果要发布）
   - 📦 构建可执行文件
   - 🚀 发布到 PyPI
   - 📝 创建 GitHub Release

4. **技术文档**：
   - [单实例运行说明](SINGLE_INSTANCE.md)
   - [对齐技巧](ALIGNMENT_TIPS.md)
   - [导出格式指南](EXPORT_FORMAT_GUIDE.md)

---

## 📖 快速导航

### 我想...

| 需求 | 文档 | 时间 |
|------|------|------|
| **快速了解怎么用** | [一页纸指南](ONE_PAGE_GUIDE.md) | 5分钟 |
| **学会基本操作** | [非技术用户指南](USER_GUIDE_NON_TECHNICAL.md) | 20分钟 |
| **安装软件** | [安装指南](INSTALL.md) 或 [非技术用户指南](USER_GUIDE_NON_TECHNICAL.md) | 10分钟 |
| **了解所有功能** | [快速开始](QUICKSTART.md) | 15分钟 |
| **解决跨平台问题** | [跨平台支持](PLATFORM_SUPPORT.md) | 按需查阅 |
| **发布软件** | [发布指南](PUBLISHING.md) | 30分钟 |
| **给同事准备安装包** | [分发建议](README_DISTRIBUTION.md) | 20分钟 |
| **了解技术细节** | [项目概览](PROJECT_OVERVIEW.md) | 30分钟 |

---

## 🎓 学习路径

### 路径 1: 非技术用户 → 熟练用户

```
第1天：ONE_PAGE_GUIDE.md (5分钟)
      ↓ 尝试录入几条数据
      
第2天：USER_GUIDE_NON_TECHNICAL.md (20分钟)
      ↓ 学习搜索和导出
      
第3天：实际使用，遇到问题查 FAQ
      ↓
      
第7天：学会批量导入
      ↓
      
第14天：完全掌握，可以教别人了！
```

### 路径 2: 技术用户 → 开发者

```
第1天：README.md + INSTALL.md (15分钟)
      ↓ 安装并运行
      
第2天：PROJECT_OVERVIEW.md (30分钟)
      ↓ 了解架构
      
第3天：阅读源码，理解实现
      ↓
      
第7天：PUBLISHING.md (30分钟)
      ↓ 学习如何发布
      
可以贡献代码了！
```

---

## 📝 文档约定

### 图标说明

- ⭐⭐⭐ - 强烈推荐，必读
- ⭐⭐ - 推荐阅读
- ⭐ - 选读
- 📄 - 文档类型
- 🎯 - 目标/用途
- ⏱️ - 预计阅读时间
- ✅ - 已测试/已验证
- ⚠️ - 注意事项
- 💡 - 提示/技巧
- 🐛 - 问题/Bug

### 用户类型标记

- 🎓 - 语言学家
- 👨‍💻 - 技术用户
- 🛠️ - 开发者
- 👨‍🏫 - 管理员

---

## 📚 外部资源

### Python 学习（如果您想深入）

- [Python 官方教程](https://docs.python.org/zh-cn/3/tutorial/)
- [廖雪峰 Python 教程](https://www.liaoxuefeng.com/wiki/1016959663602400)

### PyQt6 学习（如果您想修改界面）

- [PyQt6 官方文档](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Qt for Python 教程](https://doc.qt.io/qtforpython/)

### 语言学工具

- [ELAN](https://archive.mpi.nl/tla/elan) - 多媒体注释
- [Praat](https://www.fon.hum.uva.nl/praat/) - 语音分析
- [FieldWorks](https://software.sil.org/fieldworks/) - 语言学软件套件

---

## 🆘 找不到需要的信息？

1. **搜索关键词**：在文件中搜索关键词
2. **查看 FAQ**：各文档中的"常见问题"部分
3. **提交 Issue**：https://github.com/yourusername/fieldnote/issues
4. **联系作者**：your.email@example.com

---

## 📊 文档统计

| 类别 | 文档数 | 总字数（约） |
|------|--------|-------------|
| 用户文档 | 3 | 8,000 |
| 技术文档 | 6 | 15,000 |
| 发布文档 | 4 | 10,000 |
| **总计** | **13** | **33,000** |

---

## ✅ 文档完整性检查

维护者检查清单：

- [x] 面向非技术用户的文档
- [x] 安装指南（多种方式）
- [x] 功能使用说明
- [x] 跨平台支持文档
- [x] 发布流程文档
- [x] 技术架构文档
- [x] 故障排除指南
- [x] 常见问题解答
- [x] 示例数据
- [ ] 视频教程（建议添加）
- [ ] 带截图的图文教程（建议添加）

---

**Fieldnotes Lite** - 完善的文档体系，服务所有类型的用户！📚

