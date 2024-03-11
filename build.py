import PyInstaller.__main__

PyInstaller.__main__.run([
    'youtility/main.py',
    '--onedir',
    '--w',
    '--icon="icon.ico"'
])