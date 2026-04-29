# -*- mode: python ; coding: utf-8 -*-
import os
import sys

project_root = os.path.abspath(os.path.join(SPECPATH, '..'))

sys.path.append(project_root)
from core.version import APP_VERSION

block_cipher = None

added_files = [
    (os.path.join(project_root, 'ui/qsl_design.ui'), 'ui'), 
    (os.path.join(project_root, 'locales'), 'locales'),
    (os.path.join(project_root, 'icon.svg'), '.')
]

a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[project_root],                   
    binaries=[],
    datas=added_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=f'QSL_Generator_windows', 
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, 
    icon=[os.path.join(project_root, 'icon.ico')], # También actualizamos el ícono
)