# -*- coding: utf-8 -*-

"""Simple i18n helper for TeslaCamPlayer.

- Default language follows system locale (zh-CN -> zh, others -> en).
- Language can be overridden by config.ini: [Settings] language = zh / en.
"""

import configparser
import locale
import os

import GlobalConfig


_SUPPORTED_LANGS = ("zh", "en")
_DEFAULT_LANG = "zh"


def _detect_system_lang():
    loc = locale.getdefaultlocale()[0] or ""
    loc = loc.lower()
    if "zh" in loc:
        return "zh"
    return "en"


def _read_config_lang():
    cfg_path = GlobalConfig.CONFIG_FILE_PATH
    if not os.path.exists(cfg_path):
        return None
    cfg = configparser.ConfigParser()
    try:
        cfg.read(cfg_path, encoding="utf-8")
    except Exception:
        return None
    if not cfg.has_section("Settings"):
        return None
    lang = cfg.get("Settings", "language", fallback="").strip()
    if lang in _SUPPORTED_LANGS:
        return lang
    return None


def _write_config_lang(lang):
    if lang not in _SUPPORTED_LANGS:
        return
    cfg_path = GlobalConfig.CONFIG_FILE_PATH
    cfg = configparser.ConfigParser()
    if os.path.exists(cfg_path):
        try:
            cfg.read(cfg_path, encoding="utf-8")
        except Exception:
            cfg = configparser.ConfigParser()
    if not cfg.has_section("Settings"):
        cfg.add_section("Settings")
    cfg.set("Settings", "language", lang)
    with open(cfg_path, "w", encoding="utf-8") as f:
        cfg.write(f)


_current_lang = _read_config_lang() or _detect_system_lang() or _DEFAULT_LANG


def get_current_language():
    return _current_lang


def set_language(lang):
    global _current_lang
    if lang not in _SUPPORTED_LANGS:
        return
    _current_lang = lang
    _write_config_lang(lang)


_TEXTS = {
    "app.title": {
        "zh": "TeslaCam Player - TeslaCam播放器",
        "en": "TeslaCam Player",
    },
    # Menus
    "menu.file": {"zh": "文件", "en": "File"},
    "menu.file.open_folder": {"zh": "打开文件夹", "en": "Open Folder"},
    "menu.file.exit": {"zh": "退出", "en": "Exit"},
    "menu.settings": {"zh": "设置", "en": "Settings"},
    "menu.settings.notify": {"zh": "通知设置", "en": "Notification Settings"},
    "menu.settings.language": {"zh": "语言", "en": "Language"},
    "menu.settings.language.zh": {"zh": "中文", "en": "Chinese"},
    "menu.settings.language.en": {"zh": "英文", "en": "English"},
    "menu.help": {"zh": "帮助", "en": "Help"},
    "menu.help.check_update": {"zh": "检查更新", "en": "Check for Updates"},
    "menu.help.about": {"zh": "关于", "en": "About"},
    # About dialog
    "about.title": {"zh": "关于 TeslaCam Player", "en": "About TeslaCam Player"},
    "about.text": {
        "zh": "TeslaCam Player 是一个针对 TeslaCam / Sentry Mode 视频的桌面播放器与管理工具，支持浏览、预览、合成导出等功能。",
        "en": "TeslaCam Player is a desktop player and management tool for TeslaCam / Sentry Mode videos, supporting browse, preview and export.",
    },
    # Update check
    "update.check_failed.title": {"zh": "检查更新失败", "en": "Check for Updates Failed"},
    "update.no_new.title": {"zh": "检查更新", "en": "Check for Updates"},
    "update.no_new.text": {
        "zh": "当前已是最新版本：{current}\n最新发布：{latest}",
        "en": "You are already using the latest version: {current}\nLatest release: {latest}",
    },
    "update.has_new.title": {"zh": "发现新版本", "en": "New Version Available"},
    "update.has_new.text": {
        "zh": "检测到新版本：{latest}\n当前版本：{current}\n\n是否现在下载并安装？",
        "en": "A new version is available: {latest}\nCurrent version: {current}\n\nDownload and install now?",
    },
    "update.asset_missing.title": {"zh": "无法下载", "en": "Cannot Download"},
    "update.asset_missing.text.os": {
        "zh": "未找到与当前操作系统匹配的安装包，请前往 GitHub Releases 页面手动下载。",
        "en": "No installer matching current OS was found. Please download manually from GitHub Releases.",
    },
    "update.asset_missing.text.url": {
        "zh": "发布信息中缺少安装包下载地址，请前往 GitHub Releases 页面手动下载。",
        "en": "Download URL is missing in release assets. Please download manually from GitHub Releases.",
    },
    # Download dialog
    "download.title": {"zh": "正在下载更新", "en": "Downloading Update"},
    "download.label": {"zh": "正在下载安装包，请稍候……", "en": "Downloading installer, please wait..."},
    "download.url": {"zh": "下载链接:", "en": "URL:"},
    "download.copy": {"zh": "复制", "en": "Copy"},
    "download.path": {"zh": "保存路径:", "en": "Save to:"},
    "download.open_folder": {"zh": "打开文件夹", "en": "Open Folder"},
    "download.cancel": {"zh": "取消", "en": "Cancel"},
    "download.proxy_settings": {"zh": "代理设置...", "en": "Proxy Settings..."},
    "download.copy.ok": {"zh": "下载链接已复制到剪贴板。", "en": "Download URL has been copied to clipboard."},
    "download.folder_missing": {"zh": "文件夹不存在：{path}", "en": "Folder does not exist: {path}"},
    "download.failed.title": {"zh": "下载失败", "en": "Download Failed"},
    "download.failed.text": {"zh": "安装包下载失败：{msg}", "en": "Failed to download installer: {msg}"},
    "download.install_failed.title": {"zh": "安装启动失败", "en": "Failed to Start Installer"},
    "download.install_failed.text": {"zh": "无法启动安装程序：{msg}", "en": "Unable to start installer: {msg}"},
    # Proxy dialog
    "proxy.title": {"zh": "代理设置", "en": "Proxy Settings"},
    "proxy.enable": {"zh": "启用代理下载", "en": "Enable proxy for update download"},
    "proxy.label": {"zh": "代理地址:", "en": "Proxy URL:"},
    "proxy.placeholder": {"zh": "例如：http://127.0.0.1:7890", "en": "e.g. http://127.0.0.1:7890"},
    "proxy.hint": {
        "zh": "说明：仅用于更新下载请求，建议填写完整协议+主机+端口，例如 http://127.0.0.1:7890",
        "en": "Note: Only used for update download requests. Please use full protocol+host+port, e.g. http://127.0.0.1:7890",
    },
    "proxy.error.empty": {"zh": "已勾选启用代理，但代理地址为空。", "en": "Proxy is enabled but URL is empty."},
    "proxy.save_failed": {"zh": "写入配置文件失败：{msg}", "en": "Failed to write config file: {msg}"},
    "proxy.saved": {"zh": "代理设置已保存，下次下载时生效。", "en": "Proxy settings saved. They will take effect for the next download."},
}


def tr(key, **kwargs):
    lang = _current_lang if _current_lang in _SUPPORTED_LANGS else _DEFAULT_LANG
    entry = _TEXTS.get(key)
    if not entry:
        return key
    text = entry.get(lang) or entry.get(_DEFAULT_LANG) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
