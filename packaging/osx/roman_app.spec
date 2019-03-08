# -*- mode: python -*-

import os

from roman_analysis import get_meta

meta = get_meta(workpath)
icon = os.path.join(os.path.dirname(workpath), 'roman.icns')

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
    [],
    exclude_binaries=True,
    name='Roman',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=icon,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='Roman',
)
app = BUNDLE(
    coll,
    name='Roman.app',
    icon=icon,
    version='.'.join(meta.version.gui.split('-', 1)[0].split('.')[:3]),
    bundle_identifier='io.github.apluslms.RomanTki',
    info_plist={
        'CFBundleVersion': meta.version.full,
    })
