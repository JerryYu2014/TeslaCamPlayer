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
    # Language change
    "settings.language.saved": {
        "zh": "语言设置已保存，请重新启动应用后生效。",
        "en": "Language setting has been saved. Please restart the application to apply it.",
    },
    # VLC status / main window
    "vlc.not_installed.title": {"zh": "警告", "en": "Warning"},
    "vlc.not_installed.text": {"zh": "VLC 未安装", "en": "VLC is not installed."},
    "vlc.status.unavailable": {"zh": "VLC 不可用：VLC 未安装", "en": "VLC not available: VLC is not installed."},
    "vlc.status.available": {
        "zh": "VLC 可用，版本：{version}",
        "en": "VLC available, version: {version}",
    },
    # Generic dialog titles / messages
    "dialog.tip.title": {"zh": "提示", "en": "Information"},
    "dialog.error.title": {"zh": "错误", "en": "Error"},
    # Main processing messages (legacy CoreWorker usage)
    "process.fail": {"zh": "处理失败", "en": "Processing failed."},
    "process.done": {"zh": "处理完成", "en": "Processing finished."},
    # Notification settings dialog
    "notify.title": {"zh": "通知设置", "en": "Notification Settings"},
    "notify.system": {"zh": "系统通知", "en": "System notification"},
    "notify.group.email": {"zh": "邮件通知", "en": "Email notification"},
    "notify.group.wechat": {"zh": "微信通知", "en": "WeChat notification"},
    "notify.smtp.host": {"zh": "SMTP 主机", "en": "SMTP host"},
    "notify.smtp.port": {"zh": "SMTP 端口", "en": "SMTP port"},
    "notify.smtp.user": {"zh": "SMTP 用户", "en": "SMTP user"},
    "notify.smtp.pass": {"zh": "SMTP 密码/授权码", "en": "SMTP password / token"},
    "notify.smtp.from": {"zh": "发件人 From", "en": "Sender From"},
    "notify.smtp.to": {"zh": "收件人 To", "en": "Recipients To"},
    "notify.smtp.host.placeholder": {
        "zh": "SMTP服务器，如 smtp.qq.com",
        "en": "SMTP server, e.g. smtp.qq.com",
    },
    "notify.smtp.port.placeholder": {
        "zh": "端口，如 465 或 587",
        "en": "Port, e.g. 465 or 587",
    },
    "notify.smtp.to.placeholder": {
        "zh": "多个收件人用逗号分隔",
        "en": "Multiple recipients separated by commas",
    },
    "notify.ssl": {"zh": "使用SSL", "en": "Use SSL"},
    "notify.tls": {"zh": "使用TLS", "en": "Use TLS"},
    "notify.wechat.webhook.placeholder": {
        "zh": "企业微信机器人 Webhook URL",
        "en": "WeCom bot Webhook URL",
    },
    "notify.wechat.mentions.placeholder": {
        "zh": "需要@的手机号，逗号分隔，可留空",
        "en": "Phone numbers to @, comma separated, optional",
    },
    "notify.wechat.webhook.label": {"zh": "Webhook", "en": "Webhook"},
    "notify.wechat.mentions.label": {"zh": "@手机号", "en": "@ phone numbers"},
    "button.ok": {"zh": "确定", "en": "OK"},
    "button.cancel": {"zh": "取消", "en": "Cancel"},
    # Download dialog extra texts
    "download.cancel.in_progress": {
        "zh": "正在取消，请稍候……",
        "en": "Cancelling, please wait...",
    },
    "download.cancelled": {"zh": "已取消", "en": "Cancelled"},
    "download.manual_install.title": {
        "zh": "安装提示",
        "en": "Installation",
    },
    "download.manual_install.text": {
        "zh": "已下载安装包：{path}\n请手动运行完成安装。",
        "en": "Installer downloaded: {path}\nPlease run it manually to complete installation.",
    },
    # Player widget & context menu
    "player.menu.play": {"zh": "播放", "en": "Play"},
    "player.menu.pause": {"zh": "暂停", "en": "Pause"},
    "player.menu.stop": {"zh": "停止", "en": "Stop"},
    "player.menu.speed": {"zh": "倍数", "en": "Speed"},
    "player.menu.view": {"zh": "主视角", "en": "Main View"},
    "player.view.front": {"zh": "前", "en": "Front"},
    "player.view.back": {"zh": "后", "en": "Rear"},
    "player.view.left": {"zh": "左", "en": "Left"},
    "player.view.right": {"zh": "右", "en": "Right"},
    "player.menu.combine_export": {"zh": "合成导出", "en": "Merge & Export"},
    "player.open_folder": {"zh": "打开文件夹", "en": "Open Folder"},
    "player.play": {"zh": "播放", "en": "Play"},
    "player.pause": {"zh": "暂停", "en": "Pause"},
    # Combiner dialog
    "combiner.title": {"zh": "合成导出", "en": "Merge & Export"},
    "combiner.input_video": {"zh": "输入视频", "en": "Input video"},
    "combiner.input_video.placeholder": {"zh": "输入视频", "en": "Input video"},
    "combiner.input_video.tooltip": {
        "zh": "输入视频文件夹路径",
        "en": "Input video folder path",
    },
    "combiner.open_folder": {"zh": "打开文件夹", "en": "Open Folder"},
    "combiner.input_audio": {"zh": "输入音频", "en": "Input audio"},
    "combiner.input_audio.placeholder": {"zh": "输入音频", "en": "Input audio"},
    "combiner.input_audio.tooltip": {
        "zh": "输入音频文件路径",
        "en": "Input audio file path",
    },
    "combiner.browse": {"zh": "浏览...", "en": "Browse..."},
    "combiner.output_video": {"zh": "输出视频", "en": "Output video"},
    "combiner.output_video.placeholder": {"zh": "输出视频", "en": "Output video"},
    "combiner.output_video.tooltip": {
        "zh": "输出视频文件夹路径",
        "en": "Output video folder path",
    },
    "combiner.ffmpeg": {"zh": "FFmpeg", "en": "FFmpeg"},
    "combiner.ffmpeg.placeholder": {
        "zh": "FFmpeg安装路径(安装路径将被添加到工作环境变量PATH中)",
        "en": "FFmpeg install path (will be added to PATH)",
    },
    "combiner.ffmpeg.tooltip": {
        "zh": "FFmpeg安装路径(安装路径将被添加到工作环境变量PATH中)",
        "en": "FFmpeg install path (will be added to PATH)",
    },
    "combiner.ffmpeg.reset": {"zh": "重置", "en": "Reset"},
    "combiner.ffmpeg.reset.tooltip": {
        "zh": "重置为初始默认路径",
        "en": "Reset to initial default path",
    },
    "combiner.speed": {"zh": "输出倍速", "en": "Output speed"},
    "combiner.speed.tooltip": {"zh": "输出视频播放倍速", "en": "Playback speed of output"},
    "combiner.amap.label": {"zh": "高德地图 API Key", "en": "Amap API Key"},
    "combiner.amap.placeholder": {"zh": "输入高德地图 API Key", "en": "Enter Amap API Key"},
    "combiner.amap.tooltip": {
        "zh": "高德地图 API Key, 用于通过经纬度获取地址, 将地址添加到视频中",
        "en": "Amap API Key, used to resolve address by GPS and insert into video",
    },
    "combiner.main_view": {"zh": "主视角", "en": "Main view"},
    "combiner.main_view.placeholder": {"zh": "主视角", "en": "Main view"},
    "combiner.main_view.tooltip": {"zh": "主视角", "en": "Main view"},
    "combiner.progress": {"zh": "处理进度", "en": "Progress"},
    "combiner.start": {"zh": "开始处理", "en": "Start"},
    "combiner.loading": {"zh": "处理中，请稍候...", "en": "Processing, please wait..."},
    "combiner.ffmpeg.not_found": {
        "zh": "{folder} 路径下不存在 FFmpeg，将使用 {default} 路径下的 FFmpeg",
        "en": "No FFmpeg found under {folder}, fallback to {default}",
    },
    "combiner.ffmpeg.invalid_tesla_folder": {
        "zh": "{folder} 路径下不存在符合特斯拉行车记录仪视频文件规范的文件",
        "en": "No valid TeslaCam files found under {folder}",
    },
    "combiner.ffmpeg.default_missing": {
        "zh": "初始默认FFmpeg路径不存在",
        "en": "Initial default FFmpeg path does not exist.",
    },
    "combiner.status.ffmpeg_available": {"zh": "FFmpeg 可用", "en": "FFmpeg available"},
    "combiner.status.ffmpeg_unavailable": {"zh": "FFmpeg 不可用", "en": "FFmpeg not available"},
    "combiner.status.ffmpeg_detail": {
        "zh": "{status}：{detail}",
        "en": "{status}: {detail}",
    },
    "filedialog.select_folder": {"zh": "选择文件夹", "en": "Select Folder"},
    "filedialog.select_mp3": {"zh": "选择 mp3音频文件", "en": "Select mp3 audio file"},
    "filedialog.filter_mp3": {"zh": "MP3 文件 (*.mp3)", "en": "MP3 Files (*.mp3)"},
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
