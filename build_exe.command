#!/bin/bash
pip install pyinstaller pillow > /dev/null
pyinstaller Douyin_GUI.spec
cd dist && zip -r Douyin评论采集助手-mac.zip Douyin评论采集助手.app
