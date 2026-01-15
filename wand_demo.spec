# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules

spec_dir = os.path.abspath(os.getcwd())

hiddenimports = collect_submodules("PIL")

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
    a.binaries,
    a.zipfiles,
    a.datas,
    name="wand_demo",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,     # recommend off on Pi
    console=True,
)
