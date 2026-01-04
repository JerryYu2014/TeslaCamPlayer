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
from pathlib import Path

# 三方库
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qt_material import apply_stylesheet

# 自研库
from utils import *
import GlobalConfig
from CoreWorker import CoreWorker
from Signal import Signal
from TeslaCamPlayerWidget import TeslaCamPlayerWidget
from ThemeManager import ThemeManager, ThemeMenu
from NotificationSettingsDialog import NotificationSettingsDialog


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
            f'{GlobalConfig.APP_NAME} {GlobalConfig.APP_VERSION}')
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
        open_action = menu.addAction('打开文件夹')
        open_action.triggered.connect(
            lambda: self.browse_folder("inputType"))
        # 分隔线
        menu.addSeparator()
        # 退出
        exit_action = menu.addAction('退出')
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
        file_menu = menu_bar.addMenu("文件")
        # 打开文件夹
        open_folder_action = QAction("打开文件夹", self)
        open_folder_action.triggered.connect(
            lambda: self.browse_folder("inputType"))
        file_menu.addAction(open_folder_action)
        # 分隔线
        file_menu.addSeparator()
        # 退出
        close_action = QAction("退出", self)
        close_action.triggered.connect(sys.exit)
        file_menu.addAction(close_action)

        settings_menu = menu_bar.addMenu("设置")
        notify_action = QAction("通知设置", self)
        notify_action.triggered.connect(self.open_notification_settings)
        settings_menu.addAction(notify_action)

        # # 主题菜单
        # self.theme_menu = ThemeMenu(self.theme_manager, self)
        # menu_bar.addMenu(self.theme_menu)

        # ****** 状态栏 ******

        vlcTips = None
        if not self.teslaCamPlayerWidget.is_vlc_installed():
            vlcTips = "VLC 不可用： VLC 未安装"
            QMessageBox.warning(self, '警告', 'VLC 未安装', QMessageBox.Yes)
        else:
            vlcTips = f"VLC 可用，版本：{self.teslaCamPlayerWidget.get_libvlc_version()}"

        self.status_bar = self.statusBar()
        self.status_bar.showMessage(
            f'{GlobalConfig.APP_NAME} {GlobalConfig.APP_VERSION}，{vlcTips}', 0)

    def browse_folder(self, foldertype):
        if foldertype == "inputType":
            if self.inputFolderPath != "" and os.path.exists(self.inputFolderPath):
                folder = QFileDialog.getExistingDirectory(
                    self, "选择文件夹", self.inputFolderPath)
            else:
                folder = QFileDialog.getExistingDirectory(
                    self, "选择文件夹", os.path.expanduser('~'))
        else:
            folder = QFileDialog.getExistingDirectory(
                self, "选择文件夹", os.path.expanduser('~'))

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
                self, '提示', '处理失败', QMessageBox.Yes)
            return

        self.glogger.info(f"处理完成: {message}")

        self.loading_overlay.hide()
        QMessageBox.question(
            self, '提示', '处理完成', QMessageBox.Yes)

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
