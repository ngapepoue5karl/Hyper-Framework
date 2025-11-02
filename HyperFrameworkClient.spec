#---> NOUVEAU FICHIER .spec : HyperFrameworkClient.spec

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['hyper_framework_client/app.py'],
             pathex=['.'], 
             binaries=[],
             datas=[], # <-- LA LIGNE A ÉTÉ VIDÉE, config.ini a été retiré
             hiddenimports=[
                 'babel.numbers',
                 'pandas',
                 'pandas._libs.tslibs.base',
                 'requests',
                 'customtkinter',
                 'openpyxl',
                 'jinja2'
             ],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='HyperFrameworkClient', # Nom de l'exécutable client
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False, # Mettre à True pour le debug
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )