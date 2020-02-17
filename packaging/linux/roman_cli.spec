# -*- mode: python -*-

from roman_analysis import get_lib_meta

meta = get_lib_meta(workpath)
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
    name='roman-%s-%s' % (meta.version, meta.arch),
    debug=False,
    bootloader_ignore_signals=False,
    strip=True, # NOTE: disable, if problems are found
    upx=True, # TODO: macos ignores upx
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
