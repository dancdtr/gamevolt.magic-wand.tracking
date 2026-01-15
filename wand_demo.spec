# wand_demo.spec  (onedir)
# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules

spec_dir = os.path.abspath(os.getcwd())

hiddenimports = collect_submodules("PIL")  # Pillow

datas = [
    (os.path.join(spec_dir, "appsettings.yml"), "."),
    (os.path.join(spec_dir, "assets"), "assets"),
]

a = Analysis(
    ["main.py"],
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
    exclude_binaries=True,   # onedir pattern
    name="wand_demo",
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
    name="wand_demo",
)
