import PyInstaller.__main__
import os
import shutil

# Lösche vorherige Builds
if os.path.exists("dist"):
    shutil.rmtree("dist")
if os.path.exists("build"):
    shutil.rmtree("build")

# PyInstaller Konfiguration
PyInstaller.__main__.run([
    'bot_launcher.py',
    '--name=WordleBot',
    '--onefile',
    '--windowed',
    '--add-data=words.txt;.',
    '--add-data=cogs;cogs',
    '--add-data=dashboard;dashboard',
    '--add-data=modals;modals',
    '--add-data=models;models',
    '--add-data=utils;utils',
    '--add-data=views;views',
    '--hidden-import=discord',
    '--hidden-import=PyQt6',
    '--hidden-import=sqlalchemy',
    '--hidden-import=dotenv',
    '--clean'
]) 