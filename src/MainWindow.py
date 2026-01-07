# -*- coding: utf-8 -*-

"""
TeslaCam Player

Author: CoreMotionSpace
Date: 2025/05/16
"""

# 标准库
import os
import sys
import logging
import configparser
import tempfile
import subprocess
import webbrowser
import platform
from pathlib import Path

# 三方库
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qt_material import apply_stylesheet
import requests

# 自研库
from utils import *
import GlobalConfig
from CoreWorker import CoreWorker
from Signal import Signal
from TeslaCamPlayerWidget import TeslaCamPlayerWidget
from ThemeManager import ThemeManager, ThemeMenu
from NotificationSettingsDialog import NotificationSettingsDialog
from DownloadUpdateDialog import DownloadUpdateDialog
from I18n import tr, set_language, get_current_language


class TeslaCamPlayer(QMainWindow):
    """TeslaCam Player main window"""

    def __init__(self, master=None):
        QMainWindow.__init__(self, master)

        self.signals = Signal()

        self.current_abspath = os.path.dirname(os.path.abspath(__file__))

        # self.glogger = logger(GlobalConfig.LOG_DIR, False,
        #                       f"TeslaCamPlayer-{id(self)}")
        self.glogger = logging.getLogger("TeslaCamPlayer")

        self.inputFolderPath = ""

        # 初始化主题管理器
        self.theme_manager = ThemeManager()

        self.create_ui()
        self.read_config()

        # 读取配置后，更新主题菜单状态
        if hasattr(self, 'theme_menu'):
            self.theme_menu.update_menu_state()

        self.glogger.info(f"_MEIPASS: {hasattr(sys, '_MEIPASS')}")
        self.glogger.info(f"frozen: {getattr(sys, 'frozen', False)}")

    def create_ui(self):
        """Set up the user interface, signals & slots"""
        # 设置窗体标题
        self.setWindowTitle(
            f'{tr("app.title")} {GlobalConfig.APP_VERSION}')
        # 设置窗体大小
        self.setGeometry(0, 0, 1000, 680)
        # 设置窗体居中
        qr = self.frameGeometry()
        qr.moveCenter(QDesktopWidget().availableGeometry().center())
        self.move(qr.topLeft())
        # 设置窗口图标
        self.setWindowIcon(QIcon(self.resourcePath("assets/logo.ico")))

        # Ant Design 风格样式（仅样式，不改布局）
        # 主题色：#1890ff  文本色：#262626  边框：#d9d9d9  背景：#f5f5f5
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
                color: #262626;
                font-family: 'Microsoft YaHei', 'PingFang SC', 'Helvetica Neue', Arial;
                font-size: 10pt;
            }
            QMenuBar {
                background: #ffffff;
                border-bottom: 1px solid #d9d9d9;
            }
            QMenuBar::item {
                padding: 6px 12px;
                margin: 2px;
                border-radius: 4px;
            }
            QMenuBar::item:selected, QMenuBar::item:hover {
                background: #e6f7ff;
                color: #1890ff;
            }
            QMenu {
                background: #ffffff;
                border: 1px solid #d9d9d9;
                border-radius: 6px;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 12px;
                border-radius: 4px;
                margin: 2px;
            }
            QMenu::item:selected {
                background: #e6f7ff;
                color: #1890ff;
            }
            QStatusBar {
                background: #ffffff;
                border-top: 1px solid #d9d9d9;
                padding: 4px 8px;
                color: #595959;
            }
        """)

        # 创建托盘图标
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon(self.resourcePath("assets/logo.ico")))
        # 创建托盘菜单
        menu = QMenu()
        # 打开文件夹
        open_action = menu.addAction(tr("menu.file.open_folder"))
        open_action.triggered.connect(
            lambda: self.browse_folder("inputType"))
        # 分隔线
        menu.addSeparator()
        # 退出
        exit_action = menu.addAction(tr("menu.file.exit"))
        exit_action.triggered.connect(sys.exit)
        self.tray.setToolTip('TeslaCam Player')
        self.tray.setContextMenu(menu)
        self.tray.show()

        self.widget = QWidget(self)
        self.setCentralWidget(self.widget)

        main_layout = QHBoxLayout()
        self.teslaCamPlayerWidget = TeslaCamPlayerWidget(self.inputFolderPath)
        self.teslaCamPlayerWidget.folderChanged.connect(self.folder_changed)
        main_layout.addWidget(self.teslaCamPlayerWidget)
        self.widget.setLayout(main_layout)

        # ****** # 连接信号 ******
        self.signals.process_finish.connect(self.finishProcess)

        # ****** 工具栏 ******
        menu_bar = self.menuBar()
        # File menu
        file_menu = menu_bar.addMenu(tr("menu.file"))
        # 打开文件夹
        open_folder_action = QAction(tr("menu.file.open_folder"), self)
        open_folder_action.triggered.connect(
            lambda: self.browse_folder("inputType"))
        file_menu.addAction(open_folder_action)
        # 分隔线
        file_menu.addSeparator()
        # 退出
        close_action = QAction(tr("menu.file.exit"), self)
        close_action.triggered.connect(sys.exit)
        file_menu.addAction(close_action)

        settings_menu = menu_bar.addMenu(tr("menu.settings"))
        notify_action = QAction(tr("menu.settings.notify"), self)
        notify_action.triggered.connect(self.open_notification_settings)
        settings_menu.addAction(notify_action)

        # 语言子菜单
        language_menu = settings_menu.addMenu(tr("menu.settings.language"))
        self.action_lang_zh = QAction(
            tr("menu.settings.language.zh"), self, checkable=True)
        self.action_lang_en = QAction(
            tr("menu.settings.language.en"), self, checkable=True)

        current_lang = get_current_language()
        if current_lang == "zh":
            self.action_lang_zh.setChecked(True)
        else:
            self.action_lang_en.setChecked(True)

        self.action_lang_zh.triggered.connect(
            lambda: self.change_language("zh"))
        self.action_lang_en.triggered.connect(
            lambda: self.change_language("en"))
        language_menu.addAction(self.action_lang_zh)
        language_menu.addAction(self.action_lang_en)

        # 帮助菜单
        help_menu = menu_bar.addMenu(tr("menu.help"))
        check_update_action = QAction(tr("menu.help.check_update"), self)
        check_update_action.triggered.connect(self.check_for_updates)
        help_menu.addAction(check_update_action)

        help_menu.addSeparator()

        about_action = QAction(tr("menu.help.about"), self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

        # # 主题菜单
        # self.theme_menu = ThemeMenu(self.theme_manager, self)
        # menu_bar.addMenu(self.theme_menu)

        # ****** 状态栏 ******

        vlcTips = None
        if not self.teslaCamPlayerWidget.is_vlc_installed():
            vlcTips = tr("vlc.status.unavailable")
            QMessageBox.warning(
                self,
                tr("vlc.not_installed.title"),
                tr("vlc.not_installed.text"),
                QMessageBox.Yes,
            )
        else:
            vlcTips = tr(
                "vlc.status.available",
                version=self.teslaCamPlayerWidget.get_libvlc_version(),
            )

        self.status_bar = self.statusBar()
        self.status_bar.showMessage(
            f'{GlobalConfig.APP_NAME} {GlobalConfig.APP_VERSION}，{vlcTips}', 0)

    def browse_folder(self, foldertype):
        if foldertype == "inputType":
            if self.inputFolderPath != "" and os.path.exists(self.inputFolderPath):
                folder = QFileDialog.getExistingDirectory(
                    self, tr("filedialog.select_folder"), self.inputFolderPath)
            else:
                folder = QFileDialog.getExistingDirectory(
                    self, tr("filedialog.select_folder"), os.path.expanduser('~'))
        else:
            folder = QFileDialog.getExistingDirectory(
                self, tr("filedialog.select_folder"), os.path.expanduser('~'))

        if folder:
            if foldertype == "inputType":
                self.inputFolderPath = folder
                self.save_config()
            else:
                self.glogger.info(f"未知路径设置: {foldertype}")
        else:
            self.glogger.info("未选择文件夹")

        if folder and os.path.exists(folder):
            self.teslaCamPlayerWidget.load_all(folder)

    def resourcePath(self, relative_path):
        """获取资源文件的绝对路径"""
        # 规范化路径
        relative_path = Path(relative_path)
        if hasattr(sys, '_MEIPASS') or getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, relative_path)

        return os.path.join(self.current_abspath, relative_path)

    def startProcess(self):
        core_worker = CoreWorker(self,
                                 self.signals,
                                 self.inputFolder.text(),
                                 self.outputFolder.text())
        core_worker.start()
        self.loading_overlay.show()

    def finishProcess(self, message):
        if message == "fail":
            self.loading_overlay.hide()
            QMessageBox.question(
                self,
                tr("dialog.tip.title"),
                tr("process.fail"),
                QMessageBox.Yes,
            )
            return

        self.glogger.info(f"处理完成: {message}")

        self.loading_overlay.hide()
        QMessageBox.question(
            self,
            tr("dialog.tip.title"),
            tr("process.done"),
            QMessageBox.Yes,
        )

    def folder_changed(self, folder_path):
        self.inputFolderPath = folder_path
        self.save_config()

    def save_config(self):
        # 配置文件保存路径
        config_path = GlobalConfig.CONFIG_FILE_PATH
        if os.path.exists(config_path):
            # 如果配置文件存在就读取
            config = configparser.ConfigParser()
            config.read(config_path, encoding='utf-8')
            if not config.has_section("Settings"):
                config.add_section("Settings")
            config.set("Settings", "inputPath",
                       f"{self.inputFolderPath}")
            config.set("Settings", "theme",
                       f"{self.theme_manager.get_current_theme()}")
            try:
                ba = self.saveGeometry()
                config.set("Settings", "geometry", bytes(ba).hex())
            except Exception as ex:
                self.glogger.error(f"geometry 保存失败: {ex}")
            config.write(open(config_path, "w", encoding="utf-8"))
        else:
            # 如果没有配置文件就创建
            with open(config_path, "w", encoding="utf-8") as f:
                f.write("[Settings]\n")
                f.write(f"inputPath = {self.inputFolderPath}\n")
                f.write(f"theme = {self.theme_manager.get_current_theme()}\n")
                try:
                    ba = self.saveGeometry()
                    f.write(f"geometry = {bytes(ba).hex()}\n")
                except Exception as ex:
                    self.glogger.error(f"geometry 保存失败: {ex}")
        return True

    def read_config(self):
        # 配置文件保存路径
        config_path = GlobalConfig.CONFIG_FILE_PATH
        # 如果配置文件存在就读取
        if os.path.exists(config_path):
            config = configparser.ConfigParser()
            config.read(config_path, encoding='utf-8')
            try:
                self.inputFolderPath = config.get("Settings", "inputPath")
                if self.inputFolderPath != "" and os.path.exists(self.inputFolderPath):
                    self.teslaCamPlayerWidget.load_all(self.inputFolderPath)
            except configparser.NoOptionError as err:
                self.glogger.error(f'配置文件缺少选项: {err}')
            except Exception as ex:
                self.glogger.error(f'配置读取异常: {ex}')

            # 读取主题设置
            try:
                theme = config.get("Settings", "theme", fallback="light_blue")
                if theme in self.theme_manager.get_available_themes():
                    self.theme_manager.set_current_theme(theme)
                    self.glogger.info(f"从配置文件加载主题: {theme}")
                else:
                    self.glogger.warning(f"配置文件中的主题 {theme} 不可用，使用默认主题")
            except Exception as ex:
                self.glogger.error(f'主题配置读取异常: {ex}')

            # 读取窗口 geometry 设置
            try:
                geo = config.get("Settings", "geometry", fallback="")
                if geo:
                    ba = QByteArray(bytes.fromhex(geo))
                    self.restoreGeometry(ba)
            except Exception as ex:
                self.glogger.error(f'窗口位置读取异常: {ex}')

    def open_notification_settings(self):
        dlg = NotificationSettingsDialog(self)
        dlg.exec_()

    # ******************** 帮助菜单：关于 & 检查更新 ********************

    def change_language(self, lang: str):
        """切换应用语言并提示用户重启后生效。"""
        # 更新当前语言并写入配置文件
        set_language(lang)

        # 更新菜单勾选状态
        if lang == "zh":
            self.action_lang_zh.setChecked(True)
            self.action_lang_en.setChecked(False)
        else:
            self.action_lang_zh.setChecked(False)
            self.action_lang_en.setChecked(True)

        # 提示需要重启
        QMessageBox.information(
            self,
            tr("menu.settings.language"),
            tr("settings.language.saved"),
        )

    def show_about_dialog(self):
        """显示关于对话框"""
        text = (
            f"<b>{tr('app.title')}</b><br>"
            f"Version: {GlobalConfig.APP_VERSION}<br><br>"
            f"{tr('about.text')}"
        )
        QMessageBox.about(self, tr("about.title"), text)

    def _parse_version(self, version_str: str) -> tuple:
        """将版本号字符串解析为可比较的元组，仅提取 x.y.z 三段数字。"""
        # 例如："1.0.5 Build 2025.12.11.01" -> (1, 0, 5)
        main_part = version_str.split()[0]
        parts = []
        for p in main_part.split('.'):
            try:
                parts.append(int(p))
            except ValueError:
                parts.append(0)
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts[:3])

    def _select_asset_for_current_os(self, assets):
        """根据当前操作系统选择合适的安装包 asset。"""
        if not assets:
            return None

        if sys.platform.startswith("win"):
            # Windows: NSIS 安装包
            for a in assets:
                name = a.get("name", "")
                if name.endswith("_Setup.exe"):
                    return a
        elif sys.platform == "darwin":
            # macOS: 根据架构选择 DMG
            arch = platform.machine().lower()
            preferred_suffix = "ARM64" if "arm" in arch else "X64"
            candidates = []
            for a in assets:
                name = a.get("name", "")
                if name.endswith(".dmg") and "TeslaCamPlayer-macOS-" in name:
                    candidates.append(a)
                    if preferred_suffix in name:
                        return a
            if candidates:
                return candidates[0]

        return None

    def check_for_updates(self):
        """检查 GitHub 是否有新版本发布，并根据用户确认下载并启动安装程序。"""
        repo = "JerryYu2014/TeslaCamPlayer"
        api_url = f"https://api.github.com/repos/{repo}/releases/latest"

        try:
            resp = requests.get(api_url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as ex:
            QMessageBox.warning(self, tr("update.check_failed.title"),
                                f"{ex}")
            return

        latest_tag = data.get("tag_name") or ""
        latest_name = data.get("name") or latest_tag

        # 从 tag_name 中提取主版本号，形如 v1.0.5-2025... -> 1.0.5
        tag_version_str = latest_tag.lstrip('v').split(
            '-')[0] if latest_tag else "0.0.0"
        current_version = self._parse_version(GlobalConfig.APP_VERSION)
        latest_version = self._parse_version(tag_version_str)

        if latest_version <= current_version:
            QMessageBox.information(
                self,
                tr("update.no_new.title"),
                tr("update.no_new.text",
                   current=GlobalConfig.APP_VERSION, latest=latest_name),
            )
            return

        # 发现新版本
        reply = QMessageBox.question(
            self,
            tr("update.has_new.title"),
            tr("update.has_new.text", latest=latest_name,
               current=GlobalConfig.APP_VERSION),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )

        if reply != QMessageBox.Yes:
            return

        asset = self._select_asset_for_current_os(data.get("assets", []))
        if not asset:
            QMessageBox.warning(
                self,
                tr("update.asset_missing.title"),
                tr("update.asset_missing.text.os"),
            )
            # 打开 Releases 页面
            webbrowser.open(f"https://github.com/{repo}/releases")
            return

        url = asset.get("browser_download_url")
        name = asset.get("name", "installer")
        if not url:
            QMessageBox.warning(
                self,
                tr("update.asset_missing.title"),
                tr("update.asset_missing.text.url"),
            )
            webbrowser.open(f"https://github.com/{repo}/releases")
            return

        # 使用独立的下载进度窗体进行下载，避免主界面卡死
        dlg = DownloadUpdateDialog(self, url, name)
        dlg.exec_()

    def resizeEvent(self, event):
        # 获取屏幕分辨率
        screen = QDesktopWidget().screenGeometry()
        self.glogger.info(f"screen: {screen.width()} : {screen.height()}")

        return super().resizeEvent(event)

    def closeEvent(self, event):
        try:
            self.save_config()
        except Exception as ex:
            self.glogger.error(f'配置保存异常: {ex}')
        return super().closeEvent(event)

    def keyPressEvent(self, event):
        return super().keyPressEvent(event)


def main():
    """Entry point for TeslaCamPlayer"""
    os.makedirs(GlobalConfig.LOG_DIR, exist_ok=True)
    log_file = os.path.join(
        GlobalConfig.LOG_DIR, f"{time.strftime('%Y-%m-%d', time.localtime())}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )

    app = QApplication(sys.argv)

    # 安装 Qt 自带的中文翻译，使标准按钮文本(如 Yes/No/OK/Cancel)显示为中文
    try:
        qt_translator = QTranslator(app)
        # 优先尝试加载 qtbase 的简体中文翻译文件
        trans_path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
        if qt_translator.load("qtbase_zh_CN", trans_path):
            app.installTranslator(qt_translator)
        elif qt_translator.load("qtbase_zh_TW", trans_path):
            app.installTranslator(qt_translator)
        else:
            logging.getLogger(__name__).warning(
                "qtbase_zh_CN and qtbase_zh_TW translation not found in %s", trans_path)
    except Exception:
        logging.getLogger(__name__).exception(
            "failed to install Qt Chinese translation")

    # apply_stylesheet(app, theme='light_blue.xml')

    # 创建主窗口
    teslaCamPlayer = TeslaCamPlayer()
    # 设置主题管理器的应用程序实例
    teslaCamPlayer.theme_manager.set_app(app)
    # 应用当前主题
    current_theme = teslaCamPlayer.theme_manager.get_current_theme()
    teslaCamPlayer.theme_manager.apply_theme(current_theme)
    teslaCamPlayer.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
