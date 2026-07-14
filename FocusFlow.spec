# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\Project 2026\\TODO_APP\\FocusFlow\\main.py'],
    pathex=['D:\\Project 2026\\TODO_APP\\FocusFlow'],
    binaries=[],
    datas=[],
    hiddenimports=['PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'matplotlib.backends.backend_qtagg'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'pandas', 'scipy', 'IPython', 'notebook', 'jupyter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FocusFlow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['D:\\Project 2026\\TODO_APP\\FocusFlow\\assets\\icons\\focusflow.ico'],
)
