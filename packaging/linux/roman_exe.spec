# -*- mode: python -*-

import os
from roman_analysis import get_gui_meta

meta = get_gui_meta(workpath)
meta.datas.append((os.path.join(os.getcwd(), 'simple_gui', 'roman.png'), '.'))
block_cipher = None

a = Analysis(
    meta.exes,
    pathex=[],
    binaries=[],
    datas=meta.datas,
    hiddenimports=meta.hiddens,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Roman',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,
)
