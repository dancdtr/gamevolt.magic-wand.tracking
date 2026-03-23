# wands.spec
# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_submodules

spec_dir = os.path.abspath(os.getcwd())

hiddenimports = [
    "appsettings",
    *collect_submodules("PIL"),
]

datas = [
    (os.path.join(spec_dir, "appsettings.yml"), "."),
]

assets_dir = os.path.join(spec_dir, "assets")
if os.path.isdir(assets_dir):
    datas.append((assets_dir, "assets"))

a = Analysis(
    ["wands_main.py"],
    pathex=[spec_dir],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="wands",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="wands",
)