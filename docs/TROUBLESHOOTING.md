# Fieldnote Lite - 故障排除指南

**更新日期**: 2025-11-01

---

## 🐛 常见问题

### 问题 1: macOS 上双击打开后立即崩溃（QtCore 路径问题）⭐

**症状**: 
```
"Fieldnote" quit unexpectedly.
```

**崩溃日志显示**:
```
Thread 0 Crashed:
CoreFoundation   __CFCheckCFInfoPACSignature + 4
CoreFoundation   CFBundleCopyBundleURL + 24
QtCore           QLibraryInfoPrivate::paths(...) + 2148
```

**根本原因**:
QtCore 在初始化时无法找到 Qt 插件路径，导致空指针访问崩溃。这是 PyInstaller 打包 PyQt6 应用的**已知问题**。

**解决方案**:

#### 方案 A: 使用修复版构建脚本（推荐）⭐

```bash
# 1. 使用修复版脚本重新构建
./scripts/build_executable_fixed.sh

# 2. 测试
open dist/Fieldnote.app
```

#### 方案 B: 诊断问题

```bash
# 运行诊断脚本
./scripts/debug_crash.sh

# 查看详细错误信息
./dist/Fieldnote.app/Contents/MacOS/Fieldnote
```

#### 方案 C: 从终端运行

```bash
# 从终端运行可以看到详细错误
cd dist
./Fieldnote.app/Contents/MacOS/Fieldnote
```

#### 方案 D: 使用源码运行（临时方案）

```bash
# 不使用打包版本，直接运行源码
cd /path/to/fieldnote
poetry install
poetry run python main.py
```

---

### 问题 2: macOS 提示"无法验证开发者"

**症状**:
```
"Fieldnote" cannot be opened because the developer cannot be verified.
```

**解决方案**:

**方法 1: 右键打开**
1. 右键点击 `Fieldnote.app`
2. 选择"打开"
3. 在弹出窗口中点击"打开"

**方法 2: 系统设置**
1. 打开"系统偏好设置" → "安全性与隐私"
2. 在"通用"标签页中
3. 点击"仍要打开"按钮

**方法 3: 移除隔离属性**
```bash
xattr -cr dist/Fieldnote.app
open dist/Fieldnote.app
```

---

### 问题 3: 找不到数据库文件

**症状**:
```
FileNotFoundError: corpus.db not found
```

**原因**:
程序期望在 `~/.fieldnote/` 目录下找到数据库

**解决方案**:

```bash
# 确保目录存在
mkdir -p ~/.fieldnote

# 如果有旧的数据库，复制过来
cp corpus.db ~/.fieldnote/

# 或者在程序中使用 "新建数据库" 功能
```

---

### 问题 4: 导出 Word 文件失败

**症状**:
```
Error exporting to Word
```

**原因**:
1. python-docx 库缺失
2. 文件权限问题
3. 磁盘空间不足

**解决方案**:

```bash
# 重新安装依赖
poetry install --sync

# 检查磁盘空间
df -h

# 检查目标目录权限
ls -la ~/Downloads/
```

---

### 问题 5: 界面显示乱码或字体问题

**症状**:
- 中文显示为方框
- IPA 符号显示不正常

**解决方案**:

**macOS**:
```bash
# 安装推荐字体
brew tap homebrew/cask-fonts
brew install --cask font-charis-sil
```

**Windows**:
1. 下载 Charis SIL 字体
2. 右键 → 安装

**Linux**:
```bash
sudo apt install fonts-sil-charis
# 或
sudo dnf install sil-charis-fonts
```

---

### 问题 6: 程序启动很慢

**症状**:
第一次启动需要 10-30 秒

**原因**:
macOS 首次运行时需要验证签名和扫描文件

**解决方案**:
- 这是正常现象，第二次启动会快很多
- 如果每次都很慢，尝试：
  ```bash
  # 移除隔离属性
  xattr -cr dist/Fieldnote.app
  ```

---

### 问题 7: 无法启动多个实例

**症状**:
```
程序已在运行
```

**原因**:
单实例保护机制

**解决方案**:

**如果确实没有其他实例在运行**:
```bash
# 删除锁文件
rm /tmp/fieldnote_lite.lock
rm ~/Library/Application\ Support/Fieldnote/fieldnote_lite.lock

# 重新启动
open dist/Fieldnote.app
```

**如果想强制启动多个实例**:
```bash
# 从源码运行（不推荐）
poetry run python main.py
```

---

### 问题 8: PyInstaller 构建失败

**症状**:
```
Error: Failed to execute script PyInstaller
```

**解决方案**:

```bash
# 1. 清理旧的构建
make clean
rm -rf build dist *.spec

# 2. 重新安装 PyInstaller
poetry remove pyinstaller
poetry add --group dev pyinstaller

# 3. 使用修复版脚本
./scripts/build_executable_fixed.sh
```

---

## 🔍 诊断工具

### 查看详细日志

**macOS**:
```bash
# 查看系统崩溃报告
open ~/Library/Logs/DiagnosticReports/

# 查看控制台日志
打开"控制台.app" → 搜索 "Fieldnote"

# 从终端运行查看输出
./dist/Fieldnote.app/Contents/MacOS/Fieldnote
```

**Windows**:
```cmd
:: 查看事件查看器
eventvwr.msc

:: 从命令行运行
dist\Fieldnote\Fieldnote.exe
```

**Linux**:
```bash
# 查看系统日志
journalctl | grep -i fieldnote

# 从终端运行
./dist/Fieldnote/Fieldnote
```

### 使用诊断脚本

```bash
# 运行自动诊断
./scripts/debug_crash.sh
```

---

## 📝 收集错误信息

如果问题仍未解决，请收集以下信息并提交 Issue：

1. **系统信息**:
   ```bash
   uname -a
   python --version
   ```

2. **错误日志**:
   - 终端输出
   - 崩溃报告
   - 控制台日志

3. **构建信息**:
   ```bash
   poetry show
   pyinstaller --version
   ```

4. **重现步骤**:
   - 详细的操作步骤
   - 预期结果 vs 实际结果

5. **提交到**:
   https://github.com/ruiliapt/fieldnote/issues

---

## 🆘 获取帮助

### 在线资源

- **GitHub Issues**: https://github.com/ruiliapt/fieldnote/issues
- **Discussions**: https://github.com/ruiliapt/fieldnote/discussions
- **文档**: https://github.com/ruiliapt/fieldnote/tree/main/docs

### 临时解决方案

如果可执行文件无法正常工作，可以使用源码运行：

```bash
# 1. 克隆仓库
git clone https://github.com/ruiliapt/fieldnote.git
cd fieldnote

# 2. 安装依赖
pip install -r requirements.txt
# 或
poetry install

# 3. 运行
python main.py
# 或
poetry run python main.py
```

---

## 🔧 开发者调试

### 启用详细日志

修改 `main.py`:

```python
import sys
import logging

# 添加日志配置
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fieldnote_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    logging.info("Starting Fieldnote Lite...")
    # ... 原有代码
```

### 测试构建

```bash
# 非窗口模式（可以看到控制台输出）
poetry run pyinstaller \
    --name="Fieldnote-Debug" \
    --console \
    --debug=all \
    main.py

# 运行并查看输出
./dist/Fieldnote-Debug/Fieldnote-Debug
```

---

**还有问题？欢迎提交 Issue!** 🙋‍♂️

