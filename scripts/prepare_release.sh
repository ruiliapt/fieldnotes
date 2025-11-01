#!/bin/bash
# Fieldnote Lite - 准备 GitHub Release

VERSION="0.1.0"
RELEASE_DIR="release-v${VERSION}"

echo "=========================================="
echo "  Fieldnote Lite - 准备 GitHub Release"
echo "  版本: v${VERSION}"
echo "=========================================="
echo ""

# 清理旧的 release 目录
rm -rf "${RELEASE_DIR}"
mkdir -p "${RELEASE_DIR}"

# 1. 构建 macOS 版本
echo "📦 步骤 1/4: 构建 macOS 版本..."
./scripts/build_executable.sh

if [ -d "dist/Fieldnote.app" ]; then
    echo "✅ macOS 版本构建成功"
    
    # 创建 DMG（可选，需要 create-dmg 工具）
    # brew install create-dmg
    
    # 创建 ZIP
    echo "📦 打包 macOS 版本为 ZIP..."
    cd dist
    zip -r -q "../${RELEASE_DIR}/Fieldnote-v${VERSION}-macOS.zip" Fieldnote.app
    cd ..
    echo "✅ 已创建: ${RELEASE_DIR}/Fieldnote-v${VERSION}-macOS.zip"
else
    echo "❌ macOS 版本构建失败"
    exit 1
fi

# 2. 复制源代码
echo ""
echo "📦 步骤 2/4: 准备源代码包..."
git archive --format=zip --prefix="fieldnote-${VERSION}/" HEAD > "${RELEASE_DIR}/Source-Code-v${VERSION}.zip"
echo "✅ 已创建: ${RELEASE_DIR}/Source-Code-v${VERSION}.zip"

# 3. 生成 Release Notes
echo ""
echo "📝 步骤 3/4: 生成 Release Notes..."
cat > "${RELEASE_DIR}/RELEASE_NOTES.md" << 'EOF'
# Fieldnote Lite v0.1.0

## 🎉 首次发布！

Fieldnote Lite 是一个轻量级、跨平台的语言学田野语料管理工具。

### ✨ 核心功能

- 🌍 **跨平台支持** - Windows / macOS / Linux
- 📄 **完美 Word 导出** - 透明表格格式，符合学术规范
- ⚡ **词对词自动对齐** - 自动对齐原文和注释
- 💾 **本地数据库** - SQLite 存储，数据完全可控
- 🖥️ **现代 GUI** - PyQt6 界面，简单易用

### 📥 下载安装

#### macOS
1. 下载 `Fieldnote-v0.1.0-macOS.zip`
2. 解压缩
3. 双击 `Fieldnote.app` 启动
4. 如提示"无法验证开发者"：
   - 右键点击应用 → 选择"打开" → 点击"打开"
   - 或在"系统偏好设置" → "安全性与隐私"中允许

#### Windows / Linux
暂时请使用源代码运行：
```bash
git clone https://github.com/ruiliapt/fieldnote.git
cd fieldnote
pip install -r requirements.txt
python main.py
```

### 📖 使用指南

详见项目文档：
- [快速开始](https://github.com/ruiliapt/fieldnote/blob/main/README.md)
- [非技术用户指南](https://github.com/ruiliapt/fieldnote/blob/main/docs/user/USER_GUIDE_NON_TECHNICAL.md)
- [一页快速指南](https://github.com/ruiliapt/fieldnote/blob/main/docs/user/ONE_PAGE_GUIDE.md)

### 🐛 已知问题

- Windows 和 Linux 可执行版本待构建
- 首次启动可能较慢（正常现象）

### 🙏 反馈

如有问题或建议，欢迎：
- 提交 [Issue](https://github.com/ruiliapt/fieldnote/issues)
- 发起 [Discussion](https://github.com/ruiliapt/fieldnote/discussions)

---

**完整更新日志**: https://github.com/ruiliapt/fieldnote/blob/main/docs/developer/CHANGELOG.md
EOF

echo "✅ 已创建: ${RELEASE_DIR}/RELEASE_NOTES.md"

# 4. 显示文件信息
echo ""
echo "📦 步骤 4/4: Release 文件清单"
echo "=========================================="
ls -lh "${RELEASE_DIR}/"
echo ""

# 计算 SHA256（用于验证）
echo "🔐 文件校验和（SHA256）："
shasum -a 256 "${RELEASE_DIR}"/*.zip > "${RELEASE_DIR}/SHA256SUMS.txt"
cat "${RELEASE_DIR}/SHA256SUMS.txt"

echo ""
echo "=========================================="
echo "  ✅ Release 准备完成！"
echo "=========================================="
echo ""
echo "📦 Release 文件位于: ${RELEASE_DIR}/"
echo ""
echo "🚀 下一步：创建 GitHub Release"
echo ""
echo "方式1: 使用 GitHub CLI（推荐）"
echo "--------------------------------"
echo "1. 确保已推送代码到 GitHub："
echo "   git push origin main"
echo ""
echo "2. 创建 tag："
echo "   git tag -a v${VERSION} -m 'Release v${VERSION}'"
echo "   git push origin v${VERSION}"
echo ""
echo "3. 创建 Release："
echo "   gh release create v${VERSION} \\"
echo "       ${RELEASE_DIR}/*.zip \\"
echo "       --title 'Fieldnote Lite v${VERSION}' \\"
echo "       --notes-file ${RELEASE_DIR}/RELEASE_NOTES.md"
echo ""
echo "方式2: 使用 GitHub 网页"
echo "--------------------------------"
echo "1. 访问: https://github.com/ruiliapt/fieldnote/releases/new"
echo "2. Tag: v${VERSION}"
echo "3. Title: Fieldnote Lite v${VERSION}"
echo "4. 复制 ${RELEASE_DIR}/RELEASE_NOTES.md 的内容到描述框"
echo "5. 上传 ${RELEASE_DIR}/ 下的所有 .zip 文件"
echo "6. 点击 'Publish release'"
echo ""

