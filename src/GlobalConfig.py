# -*- coding: utf-8 -*-

# 标准库
import os
import sys


def get_writable_path(folder_name):
    """获取可写的文件夹路径"""
    if hasattr(sys, '_MEIPASS') or getattr(sys, 'frozen', False):
        # 打包后，使用用户文档目录
        base_path = os.path.expanduser("~/Documents")
    else:
        # 未打包，使用当前目录
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.join(base_path, folder_name)


APP_NAME = "TeslaCam Player - TeslaCam播放器"
# APP_VERSION = "1.0.5 Build 2025.12.11.01"
APP_VERSION = "1.0.8"
APP_PATH = get_writable_path("")


if hasattr(sys, '_MEIPASS') or getattr(sys, 'frozen', False):
    APP_FOLDER = "TeslaCamPlayer"
else:
    APP_FOLDER = ""

APP_FOLDER_PATH = os.path.join(APP_PATH, APP_FOLDER)
os.makedirs(APP_FOLDER_PATH, exist_ok=True)

# *** APP 目录 ***

TEMPS_DIR = os.path.join(APP_FOLDER_PATH, "temps")
os.makedirs(TEMPS_DIR, exist_ok=True)

LOG_DIR = os.path.join(APP_FOLDER_PATH, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# *** APP 用户目录 ***

USER_DIR = os.path.join(os.path.expanduser('~'), ".teslaCamPlayer")
os.makedirs(USER_DIR, exist_ok=True)

CONFIG_FILE = "config.ini"
CONFIG_FILE_PATH = os.path.join(USER_DIR, CONFIG_FILE)
