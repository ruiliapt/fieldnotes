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

# 过滤掉导致崩溃的 Qt 权限插件
a.binaries = [x for x in a.binaries if not ('qdarwinpermission' in x[0].lower() or 'locationpermission' in x[0].lower())]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Fieldnote',
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
    name='Fieldnote',
)
app = BUNDLE(
    coll,
    name='Fieldnote.app',
    icon=None,
    bundle_identifier='com.linguistics.fieldnote',
)
