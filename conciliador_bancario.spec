# conciliador_bancario.spec
# PyInstaller 6.x — modo onefile, Windows

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

a = Analysis(
    ['gui/app.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        *collect_data_files('customtkinter'),
    ],
    hiddenimports=[
        *collect_submodules('customtkinter'),
        'babel.numbers',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'pygments',
        '_pytest',
    ],
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
    name='ConciliadorBancario',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)