# 跨平台打包指南

本文档说明如何在 Windows、Linux 和 macOS 平台上构建 Fieldnotes Lite 的可执行文件。

---

## 📋 平台特定说明

### ⚠️ 重要提示

**PyInstaller 的限制**：
- ❌ 不支持跨平台编译
- ✅ 必须在目标平台上进行打包
- 例如：Windows 版本必须在 Windows 上打包，Linux 版本必须在 Linux 上打包

---

## 🍎 macOS 打包

### 前置要求
```bash
# 已安装 Python 3.11+
python3 --version

# 已安装 Poetry
poetry --version
```

### 打包步骤

```bash
# 1. 克隆仓库
git clone https://github.com/ruiliapt/fieldnote.git
cd fieldnote

# 2. 安装依赖
poetry install

# 3. 执行打包脚本
bash scripts/build_executable.sh
```

### 输出结果
- **位置**: `dist/Fieldnotes.app`
- **类型**: macOS 应用程序包
- **分发**: `tar -czf Fieldnote-macOS.tar.gz dist/Fieldnotes.app`

### 测试
```bash
# 直接打开
open dist/Fieldnotes.app

# 或命令行启动
./dist/Fieldnotes.app/Contents/MacOS/Fieldnotes
```

---

## 🪟 Windows 打包

### 前置要求
```powershell
# 已安装 Python 3.11+
python --version

# 已安装 Poetry
poetry --version
```

### 打包步骤

```powershell
# 1. 克隆仓库
git clone https://github.com/ruiliapt/fieldnote.git
cd fieldnote

# 2. 安装依赖
poetry install

# 3. 执行打包脚本
scripts\build_executable.bat
```

### 输出结果
- **位置**: `dist\Fieldnotes\Fieldnotes.exe`
- **类型**: Windows 可执行文件 + 依赖文件夹
- **分发**: 压缩整个 `dist\Fieldnotes\` 文件夹为 ZIP

### 创建分发包
```powershell
# 使用 PowerShell 压缩
Compress-Archive -Path dist\Fieldnotes -DestinationPath Fieldnote-Windows.zip

# 或使用 7-Zip（如已安装）
7z a -tzip Fieldnote-Windows.zip dist\Fieldnotes\*
```

### 测试
```powershell
# 直接运行
dist\Fieldnotes\Fieldnotes.exe

# 创建桌面快捷方式
# 右键 Fieldnotes.exe -> 发送到 -> 桌面快捷方式
```

### Windows 特定注意事项

1. **杀毒软件警告**
   - PyInstaller 打包的程序可能触发杀毒软件警告
   - 建议用户添加到白名单

2. **管理员权限**
   - 首次运行可能需要管理员权限
   - 或右键选择"以管理员身份运行"

3. **字体支持**
   - 确保系统已安装 Doulos SIL 和 Charis SIL 字体
   - 下载地址：https://software.sil.org/fonts/

---

## 🐧 Linux 打包

### 前置要求
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Arch Linux
sudo pacman -S python python-pip

# Fedora
sudo dnf install python3 python3-pip

# 安装 Poetry
curl -sSL https://install.python-poetry.org | python3 -
```

### 打包步骤

```bash
# 1. 克隆仓库
git clone https://github.com/ruiliapt/fieldnote.git
cd fieldnote

# 2. 安装依赖
poetry install

# 3. 执行打包脚本
bash scripts/build_executable.sh
```

### 输出结果
- **位置**: `dist/Fieldnotes/Fieldnotes`
- **类型**: Linux 可执行文件 + 依赖文件夹
- **架构**: 根据编译机器（x86_64、arm64 等）

### 创建分发包
```bash
# 创建 tar.gz 包
cd dist
tar -czf Fieldnote-Linux-$(uname -m).tar.gz Fieldnotes/

# 示例输出：
# Fieldnote-Linux-x86_64.tar.gz
# Fieldnote-Linux-aarch64.tar.gz
```

### 测试
```bash
# 添加执行权限（如需要）
chmod +x dist/Fieldnotes/Fieldnotes

# 运行
./dist/Fieldnotes/Fieldnotes
```

### Linux 特定注意事项

1. **依赖库**
   ```bash
   # Ubuntu/Debian 可能需要
   sudo apt install libxcb-xinerama0 libxcb-cursor0
   
   # 如果缺少 Qt 库
   sudo apt install libqt6widgets6 libqt6gui6 libqt6core6
   ```

2. **桌面集成**
   创建 `.desktop` 文件：
   ```bash
   cat > ~/.local/share/applications/fieldnotes.desktop << EOF
   [Desktop Entry]
   Name=Fieldnotes Lite
   Comment=田野笔记管理工具
   Exec=/path/to/Fieldnotes/Fieldnotes
   Icon=/path/to/icon.png
   Terminal=false
   Type=Application
   Categories=Office;Education;
   EOF
   ```

3. **字体安装**
   ```bash
   # 下载并安装 SIL 字体
   mkdir -p ~/.fonts
   # 下载字体文件到 ~/.fonts/
   fc-cache -f -v
   ```

---

## 📦 发布检查清单

### 打包前
- [ ] 更新版本号（`pyproject.toml`）
- [ ] 更新 `README.md`
- [ ] 更新 `CHANGELOG`
- [ ] 测试所有核心功能
- [ ] 提交所有代码到 Git

### 各平台打包
- [ ] **macOS**: 在 macOS 上打包并测试
- [ ] **Windows**: 在 Windows 上打包并测试
- [ ] **Linux**: 在 Linux 上打包并测试（建议多个发行版）

### 打包后测试
- [ ] 启动程序
- [ ] 创建数据库
- [ ] 录入数据
- [ ] 导出 Word
- [ ] 字体显示正确
- [ ] 小型大写转换
- [ ] 数据分类功能

### 发布
- [ ] 创建 GitHub Release
- [ ] 上传各平台安装包
- [ ] 添加校验和（SHA256）
- [ ] 更新发布说明

---

## 🔍 常见问题

### Q1: 如何在没有对应平台的情况下打包？

**A**: 有以下几种方案：

1. **使用虚拟机**
   - VMware / VirtualBox 安装目标系统
   - 在虚拟机中打包

2. **使用云服务器**
   - AWS / Azure / Alibaba Cloud
   - 租用临时服务器打包

3. **使用 GitHub Actions** ⭐ 推荐
   - 配置 CI/CD 自动打包
   - 支持 Windows、Linux、macOS
   - 参考 `.github/workflows/build.yml`（待创建）

### Q2: 打包文件太大怎么办？

**A**: PyInstaller 会打包所有依赖，文件较大是正常的。可以：
- 使用 `--onefile` 模式（单文件，但启动慢）
- 使用 UPX 压缩（可减少 30-50% 大小）
- 排除不需要的模块

### Q3: 是否支持便携版？

**A**: 是的，打包后的程序本身就是便携的：
- 不写注册表（Windows）
- 不依赖系统安装
- 数据库文件在程序目录或用户指定位置

### Q4: 如何设置程序图标？

**A**: 修改打包脚本：
```bash
# macOS/Linux
pyinstaller --icon=icon.icns ...

# Windows
pyinstaller --icon=icon.ico ...
```

---

## 📊 打包大小参考

| 平台 | 压缩前 | 压缩后 |
|------|--------|--------|
| macOS | ~200 MB | ~50 MB |
| Windows | ~150 MB | ~40 MB |
| Linux | ~180 MB | ~45 MB |

---

## 🔗 相关资源

- [PyInstaller 文档](https://pyinstaller.org/)
- [Poetry 文档](https://python-poetry.org/)
- [PyQt6 文档](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [SIL 字体下载](https://software.sil.org/fonts/)

---

## 🤝 贡献

如果您成功在某个平台上打包，欢迎：
1. 分享打包经验
2. 提交 Pull Request 改进打包脚本
3. 报告平台特定问题

---

**最后更新**: 2025-11-02

