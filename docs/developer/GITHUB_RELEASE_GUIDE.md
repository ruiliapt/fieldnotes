# GitHub Release 发布指南

**创建日期**: 2025-11-01  
**适用版本**: Fieldnote Lite v0.1.0+

---

## 🎯 概述

本指南说明如何在 GitHub 上发布 Fieldnote Lite 的可执行版本。

---

## 📋 发布前检查清单

- [ ] 代码已推送到 GitHub
- [ ] 版本号已更新（`pyproject.toml`）
- [ ] CHANGELOG 已更新
- [ ] 所有测试通过
- [ ] 可执行文件已构建并测试

---

## 🚀 快速发布（推荐）

### 方式 1: 使用自动化脚本 ⭐

```bash
# 1. 准备 Release 文件
./scripts/prepare_release.sh

# 2. 推送代码和创建 tag
git push origin main
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0

# 3. 创建 Release（需要 GitHub CLI）
gh release create v0.1.0 \
    release-v0.1.0/*.zip \
    --title "Fieldnote Lite v0.1.0" \
    --notes-file release-v0.1.0/RELEASE_NOTES.md
```

---

## 📝 详细步骤

### 步骤 1: 准备可执行文件

#### macOS

```bash
# 构建 .app
./scripts/build_executable.sh

# 打包为 ZIP
cd dist
zip -r Fieldnote-v0.1.0-macOS.zip Fieldnote.app
cd ..
```

#### Windows（在 Windows 环境）

```cmd
:: 构建 .exe
scripts\build_executable.bat

:: 打包为 ZIP
cd dist
tar -a -c -f Fieldnote-v0.1.0-Windows.zip Fieldnote
cd ..
```

#### Linux

```bash
# 构建
./scripts/build_executable.sh

# 打包
cd dist
tar -czf Fieldnote-v0.1.0-Linux.tar.gz Fieldnote/
cd ..
```

### 步骤 2: 创建 Git Tag

```bash
# 创建带注释的 tag
git tag -a v0.1.0 -m "Release v0.1.0

- 跨平台语料管理
- Word 透明表格导出
- 词对词自动对齐
"

# 查看 tag
git tag -l -n

# 推送 tag 到 GitHub
git push origin v0.1.0
```

### 步骤 3: 在 GitHub 创建 Release

#### 方法 A: 使用 GitHub CLI（推荐）⭐

```bash
# 安装 GitHub CLI（如果未安装）
brew install gh  # macOS
# 或访问 https://cli.github.com/

# 登录
gh auth login

# 创建 Release
gh release create v0.1.0 \
    release-v0.1.0/Fieldnote-v0.1.0-macOS.zip \
    release-v0.1.0/Source-Code-v0.1.0.zip \
    --title "Fieldnote Lite v0.1.0" \
    --notes-file release-v0.1.0/RELEASE_NOTES.md

# 可选：添加更多文件
gh release upload v0.1.0 \
    release-v0.1.0/Fieldnote-v0.1.0-Windows.zip \
    release-v0.1.0/Fieldnote-v0.1.0-Linux.tar.gz
```

#### 方法 B: 使用 GitHub 网页

1. **访问 Releases 页面**
   ```
   https://github.com/ruiliapt/fieldnote/releases/new
   ```

2. **填写信息**
   - **Tag**: 选择或输入 `v0.1.0`
   - **Target**: `main` 分支
   - **Title**: `Fieldnote Lite v0.1.0`
   - **Description**: 复制 `release-v0.1.0/RELEASE_NOTES.md` 的内容

3. **上传文件**
   - 点击 "Attach binaries" 区域
   - 上传所有 `.zip` 和 `.tar.gz` 文件

4. **发布**
   - 勾选 "Set as a pre-release"（如果是测试版）
   - 点击 "Publish release"

---

## 📄 Release Notes 模板

```markdown
# Fieldnote Lite v0.1.0

## 🎉 首次发布！

### ✨ 主要功能

- 🌍 跨平台支持
- 📄 Word 透明表格导出
- ⚡ 词对词自动对齐
- 💾 本地 SQLite 数据库

### 📥 下载

#### macOS
- 下载 `Fieldnote-v0.1.0-macOS.zip`
- 解压并双击 `Fieldnote.app`

#### Windows
- 下载 `Fieldnote-v0.1.0-Windows.zip`
- 解压并运行 `Fieldnote.exe`

#### Linux
- 下载 `Fieldnote-v0.1.0-Linux.tar.gz`
- 解压并运行 `./Fieldnote/Fieldnote`

### 📖 文档

- [README](https://github.com/ruiliapt/fieldnote)
- [用户指南](https://github.com/ruiliapt/fieldnote/blob/main/docs/user/USER_GUIDE_NON_TECHNICAL.md)

### 🐛 已知问题

- 首次启动可能较慢
- macOS 可能需要在"安全性与隐私"中允许

### 🙏 反馈

欢迎提交 [Issue](https://github.com/ruiliapt/fieldnote/issues)

---

**完整更新日志**: [CHANGELOG.md](https://github.com/ruiliapt/fieldnote/blob/main/docs/developer/CHANGELOG.md)
```

---

## 🔐 验证和签名（可选）

### 生成校验和

```bash
# SHA256
shasum -a 256 release-v0.1.0/*.zip > SHA256SUMS.txt

# MD5
md5 release-v0.1.0/*.zip > MD5SUMS.txt
```

### macOS 代码签名（需要 Apple 开发者账号）

```bash
# 签名
codesign --force --deep --sign "Developer ID Application: Your Name" \
    dist/Fieldnote.app

# 公证（notarization）
xcrun notarytool submit dist/Fieldnote.zip \
    --apple-id your@email.com \
    --team-id TEAMID \
    --password app-specific-password
```

---

## 📊 发布后检查

- [ ] Release 页面显示正常
- [ ] 下载链接有效
- [ ] 文件可以正常下载解压
- [ ] 在干净的系统上测试运行
- [ ] 社交媒体宣传（可选）

---

## 🔄 更新已有 Release

### 添加文件

```bash
gh release upload v0.1.0 new-file.zip
```

### 修改 Release Notes

```bash
gh release edit v0.1.0 --notes "新的说明"
```

### 删除 Release

```bash
# 删除 Release（保留 tag）
gh release delete v0.1.0

# 删除 tag
git tag -d v0.1.0
git push origin :refs/tags/v0.1.0
```

---

## 🎯 最佳实践

### 1. 版本号规范

遵循 [语义化版本](https://semver.org/lang/zh-CN/)：

```
主版本号.次版本号.修订号

v0.1.0 - 初始版本
v0.1.1 - Bug 修复
v0.2.0 - 新功能
v1.0.0 - 稳定版本
```

### 2. Tag 命名

```bash
# ✅ 推荐
v0.1.0
v1.0.0-beta
v2.0.0-rc1

# ❌ 不推荐
0.1.0
release-0.1.0
```

### 3. Release 类型

- **Latest release** - 最新稳定版
- **Pre-release** - 测试版（alpha, beta, rc）
- **Draft** - 草稿（未发布）

### 4. 文件命名

```
Fieldnote-v{版本号}-{平台}.{格式}

示例：
Fieldnote-v0.1.0-macOS.zip
Fieldnote-v0.1.0-Windows.zip
Fieldnote-v0.1.0-Linux.tar.gz
```

---

## 🆘 常见问题

### Q: 如何撤销已发布的 Release？

```bash
# 删除 Release
gh release delete v0.1.0 --yes

# 删除 tag
git tag -d v0.1.0
git push origin :refs/tags/v0.1.0
```

### Q: Release 文件太大怎么办？

- GitHub 单个文件限制：2 GB
- Release 总大小限制：较宽松，但建议 < 500 MB
- 可以使用 GitHub Releases 的 CDN 链接

### Q: 如何创建多平台 Release？

1. 在各平台分别构建
2. 收集所有构建产物
3. 一次性上传所有平台的文件

或使用 CI/CD（GitHub Actions）自动构建。

---

## 🔗 相关链接

- [GitHub Releases 文档](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [GitHub CLI 文档](https://cli.github.com/manual/)
- [语义化版本](https://semver.org/lang/zh-CN/)

---

**祝发布顺利！** 🎉

