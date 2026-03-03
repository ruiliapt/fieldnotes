# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata

datas = [('README.md', '.')]
datas += copy_metadata('PyQt6')
datas += copy_metadata('PyQt6-Qt6')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.sip', 'docx', 'docx.oxml', 'docx.oxml.ns', 'pandas', 'sqlite3', 'database', 'gui', 'exporter'],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=['hooks/rthook_qt_permissions.py'],
    excludes=['PyQt6.QtPositioning', 'PyQt6.QtLocation', 'PyQt6.QtBluetooth'],
    noarchive=False,
    optimize=0,
)

# 过滤掉导致崩溃的 Qt 权限插件和相关文件
def filter_binaries(binaries):
    excluded_patterns = [
        'qdarwinpermission',
        'locationpermission',
        'qdarwin',  # 所有 Darwin 平台特定的权限插件
        'permission',  # 所有权限相关插件
    ]
    filtered = []
    for name, path, typecode in binaries:
        name_lower = name.lower()
        path_lower = path.lower() if path else ""
        
        # 检查是否匹配排除模式
        should_exclude = any(
            pattern in name_lower or pattern in path_lower 
            for pattern in excluded_patterns
        )
        
        if not should_exclude:
            filtered.append((name, path, typecode))
        else:
            print(f"🚫 Excluding problematic file: {name}")
    return filtered

a.binaries = filter_binaries(a.binaries)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Fieldnotes',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Fieldnotes',
)
app = BUNDLE(
    coll,
    name='Fieldnotes.app',
    icon=None,
    bundle_identifier='com.linguistics.fieldnote',
    version='0.4.0',
    info_plist={
        'CFBundleShortVersionString': '0.4.0',
        'CFBundleVersion': '0.4.0',
        'CFBundleName': 'Fieldnotes',
        'CFBundleDisplayName': 'Fieldnotes Lite',
        'CFBundlePackageType': 'APPL',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13.0',
    },
)
