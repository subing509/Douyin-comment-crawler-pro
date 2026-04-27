# -*- mode: python -*-
import PyInstaller.__main__
PyInstaller.__main__.run([
    'gui.py',
    '--onefile',
    '--windowed',
    '--name=Douyin评论采集助手',
    '--clean',
    '--noconfirm'
])
