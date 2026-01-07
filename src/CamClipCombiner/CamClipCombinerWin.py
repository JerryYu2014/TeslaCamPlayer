# -*- coding: utf-8 -*-

"""
TeslaCam Clip Combiner

Author: CoreMotionSpace
Date: 2025/03/09
"""

import os
import sys
import shutil
import logging
import platform
import configparser
from pathlib import Path

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# from utils import *
import GlobalConfig
from I18n import tr
from CamClipCombiner.CoreWorker import CoreWorker
from Signal import Signal
from notifier import Notifier

# 解决MacOS系统中因 pyinstaller 构建安装包后无法获取全量环境变量，
# 从而导致FFmpeg无法使用的问题，通过设置环境变量来解决
if platform.system() == 'Darwin':
    # 添加FFmpeg路径的工作环境变量，该路径下的FFmpeg为通过 brew 安装的默认路径
    FFMPEG_HOME = '/usr/local/bin'
    PATH = os.environ['PATH']
    os.environ['PATH'] = f'{FFMPEG_HOME}:{PATH}'


class CamClipCombiner(QDialog):
    """TeslaCam Clip Combiner dialog"""

    def __init__(self, master=None, input_folder_path: str = ""):
        QDialog.__init__(self, master)

        self.signals = Signal()
        self.current_abspath = os.path.dirname(os.path.abspath(__file__))
        # self.glogger = logger(GlobalConfig.LOG_DIR, False,
        #                       f"CamClipCombiner-{id(self)}")
        self.glogger = logging.getLogger("CamClipCombiner")
        # PATH = os.environ['PATH']
        # self.glogger.info(f"PATH: {PATH}")
        # 初始默认FFmpeg路径
        self.init_default_ffmpeg_path = self.get_default_ffmpeg_path()
        self.core_worker = None
        self.main_view = 'front'
        self.notifier = None

        # 从主窗体传入的输入视频文件夹路径
        self.input_folder_path_from_main = input_folder_path

        # 若有父窗口，则作为模态子窗体使用
        if master is not None:
            self.setWindowModality(Qt.ApplicationModal)

        self.create_ui()
        self.read_config()
        self._init_notifier_from_config()

        self.glogger.info(f"_MEIPASS: {hasattr(sys, '_MEIPASS')}")
        self.glogger.info(f"frozen: {getattr(sys, 'frozen', False)}")

    def create_ui(self):
        """Set up the user interface, signals & slots"""

        # 设置窗体标题
        self.setWindowTitle(tr("combiner.title"))
        # 设置窗体大小
        self.resize(900, 360)
        # 设置窗体居中
        qr = self.frameGeometry()
        qr.moveCenter(QDesktopWidget().availableGeometry().center())
        self.move(qr.topLeft())

        # 对话框主布局
        self.vBox = QVBoxLayout(self)

        # 输入视频
        inputFolderHLayout = QHBoxLayout()
        inputFolderLbl = QLabel(tr("combiner.input_video"), self)
        inputFolderHLayout.addWidget(inputFolderLbl)
        self.inputFolder = QLineEdit(self)
        self.inputFolder.setPlaceholderText(tr("combiner.input_video.placeholder"))
        self.inputFolder.setToolTip(tr("combiner.input_video.tooltip"))
        # 使用主窗体传入的文件夹路径
        if self.input_folder_path_from_main and os.path.exists(self.input_folder_path_from_main):
            self.inputFolder.setText(self.input_folder_path_from_main)
        else:
            self.inputFolder.setText("")
        # 设置只读
        self.inputFolder.setReadOnly(True)
        inputFolderHLayout.addWidget(self.inputFolder)
        # 打开文件夹按钮
        self.openInputFolderBtn = QPushButton(tr("combiner.open_folder"), self)
        self.openInputFolderBtn.clicked.connect(self.openInputPath)
        inputFolderHLayout.addWidget(self.openInputFolderBtn)
        # # 播放按钮
        # self.playBtn = QPushButton("播放")
        # self.playBtn.clicked.connect(self.play)
        # inputFolderHLayout.addWidget(self.playBtn)
        self.vBox.addLayout(inputFolderHLayout)

        # 输入音频
        audioFilePathHLayout = QHBoxLayout()
        audioFileLbl = QLabel(tr("combiner.input_audio"), self)
        audioFilePathHLayout.addWidget(audioFileLbl)
        self.audioFilePath = QLineEdit(self)
        self.audioFilePath.setPlaceholderText(tr("combiner.input_audio.placeholder"))
        self.audioFilePath.setToolTip(tr("combiner.input_audio.tooltip"))
        self.audioFilePath.setText(GlobalConfig.TEMPS_DIR)
        # 设置只读
        self.audioFilePath.setReadOnly(True)
        audioFilePathHLayout.addWidget(self.audioFilePath)
        # 添加浏览文件夹按钮
        self.audioFileBrowseBtn = QPushButton(tr("combiner.browse"), self)
        self.audioFileBrowseBtn.clicked.connect(self.openAudioFile)
        audioFilePathHLayout.addWidget(self.audioFileBrowseBtn)
        # 打开文件夹按钮
        # self.audioFileBtn = QPushButton("查看文件夹", self)
        # self.audioFileBtn.clicked.connect(self.openAudioPath)
        # audioFilePathHLayout.addWidget(self.audioFileBtn)
        self.vBox.addLayout(audioFilePathHLayout)

        # 输出视频
        outputFolderHLayout = QHBoxLayout()
        outputFolderLbl = QLabel(tr("combiner.output_video"), self)
        outputFolderHLayout.addWidget(outputFolderLbl)
        self.outputFolder = QLineEdit(self)
        self.outputFolder.setPlaceholderText(tr("combiner.output_video.placeholder"))
        self.outputFolder.setToolTip(tr("combiner.output_video.tooltip"))
        self.outputFolder.setText(GlobalConfig.TEMPS_DIR)
        # 设置只读
        self.outputFolder.setReadOnly(True)
        outputFolderHLayout.addWidget(self.outputFolder)
        # 添加浏览文件夹按钮
        self.outputBrowseBtn = QPushButton(tr("combiner.browse"), self)
        self.outputBrowseBtn.clicked.connect(
            lambda: self.browseFolder("outputType"))
        outputFolderHLayout.addWidget(self.outputBrowseBtn)
        # 打开文件夹按钮
        self.openOutputFolderBtn = QPushButton(tr("combiner.open_folder"), self)
        self.openOutputFolderBtn.clicked.connect(self.openOutputPath)
        outputFolderHLayout.addWidget(self.openOutputFolderBtn)
        self.vBox.addLayout(outputFolderHLayout)

        # FFmpeg路径
        ffmpegPathHLayout = QHBoxLayout()
        ffmpegPathLbl = QLabel(tr("combiner.ffmpeg"), self)
        ffmpegPathHLayout.addWidget(ffmpegPathLbl)
        self.ffmpegPath = QLineEdit(self)
        self.ffmpegPath.setPlaceholderText(tr("combiner.ffmpeg.placeholder"))
        self.ffmpegPath.setToolTip(tr("combiner.ffmpeg.tooltip"))
        self.ffmpegPath.textChanged.connect(self.ffmpegPathChanged)
        self.ffmpegPath.setReadOnly(True)
        ffmpegPathHLayout.addWidget(self.ffmpegPath)
        # 添加浏览文件夹按钮
        self.ffmpegBrowseBtn = QPushButton(tr("combiner.browse"), self)
        self.ffmpegBrowseBtn.clicked.connect(
            lambda: self.browseFolder("ffmpegType"))
        ffmpegPathHLayout.addWidget(self.ffmpegBrowseBtn)
        # 重置
        self.resetFFmpegPathBtn = QPushButton(tr("combiner.ffmpeg.reset"), self)
        self.resetFFmpegPathBtn.setToolTip(tr("combiner.ffmpeg.reset.tooltip"))
        self.resetFFmpegPathBtn.clicked.connect(self.resetFFmpegPath)
        ffmpegPathHLayout.addWidget(self.resetFFmpegPathBtn)
        self.vBox.addLayout(ffmpegPathHLayout)

        # 其他配置
        othersHLayout = QHBoxLayout()
        # 输出倍速
        tripleSpeedLbl = QLabel(tr("combiner.speed"), self)
        othersHLayout.addWidget(tripleSpeedLbl)
        self.tripleSpeed = QDoubleSpinBox(self)
        self.tripleSpeed.setToolTip(tr("combiner.speed.tooltip"))
        self.tripleSpeed.setRange(0.1, 10)
        self.tripleSpeed.setValue(10)
        self.tripleSpeed.setSingleStep(0.1)
        self.tripleSpeed.valueChanged.connect(self.tripleSpeedChanged)
        othersHLayout.addWidget(self.tripleSpeed)
        # 高德地图 API Key
        amapApiKeyLbl = QLabel(tr("combiner.amap.label"), self)
        othersHLayout.addWidget(amapApiKeyLbl)
        self.amapApiKey = QLineEdit(self)
        self.amapApiKey.setPlaceholderText(tr("combiner.amap.placeholder"))
        self.amapApiKey.setToolTip(tr("combiner.amap.tooltip"))
        self.amapApiKey.setMaxLength(32)
        self.amapApiKey.setMinimumWidth(260)
        # 只允许字母和数字
        self.amapApiKey.setValidator(QRegExpValidator(QRegExp("[A-Za-z0-9]*")))
        self.amapApiKey.textChanged.connect(self.amapApiKeyChanged)
        othersHLayout.addWidget(self.amapApiKey)
        # 主视角
        mainViewLbl = QLabel(tr("combiner.main_view"), self)
        othersHLayout.addWidget(mainViewLbl)
        self.mainViewBox = QComboBox()
        self.mainViewBox.setPlaceholderText(tr("combiner.main_view.placeholder"))
        self.mainViewBox.setToolTip(tr("combiner.main_view.tooltip"))
        self.mainViewBox.addItems([
            tr("player.view.front"),
            tr("player.view.back"),
            tr("player.view.left"),
            tr("player.view.right"),
        ])
        self.mainViewBox.setMinimumWidth(100)
        self.mainViewBox.setCurrentText(tr("player.view.front"))
        self.mainViewBox.currentTextChanged.connect(
            lambda text: self.setMainView(text))
        othersHLayout.addWidget(self.mainViewBox)
        othersHLayout.addStretch(1)
        self.vBox.addLayout(othersHLayout)

        procProgHLayout = QHBoxLayout()
        # 处理进度条
        procProgLbl = QLabel(tr("combiner.progress"), self)
        procProgHLayout.addWidget(procProgLbl)
        self.procProgBar = QProgressBar(self)
        self.procProgBar.setRange(0, 100)
        self.procProgBar.setValue(0)
        procProgHLayout.addWidget(self.procProgBar)
        # self.cancProcBtn = QPushButton("取消", self)
        # self.cancProcBtn.setFixedHeight(24)
        # self.cancProcBtn.clicked.connect(self.cancelProcess)
        # procProgHLayout.addWidget(self.cancProcBtn)
        self.vBox.addLayout(procProgHLayout)

        # 底部
        bottom_hlayout = QHBoxLayout()
        bottom_hlayout.addStretch(1)
        # 处理按钮
        self.handlebtn = QPushButton(tr("combiner.start"))
        self.handlebtn.clicked.connect(self.startProcess)
        bottom_hlayout.addWidget(self.handlebtn)
        self.vBox.addLayout(bottom_hlayout)

        # ****** 为避免保存配置时部分组件还未被初始化问题 ******
        self.ffmpegPath.setText(self.get_default_ffmpeg_path())

        # ****** 连接信号 ******
        self.signals.process_finish.connect(self.finishProcess)
        self.signals.process_progress.connect(self.updateProcessProgress)

        # ****** 处理中提示 ******
        # 处理中的覆盖层（初始隐藏）
        self.loading_overlay = QWidget(self)
        self.loading_overlay.setStyleSheet("""
            background-color: rgba(0, 0, 0, 100);
        """)
        self.loading_overlay.hide()
        self.loading_overlay.resize(self.size())

        # 处理提示布局
        loading_layout = QVBoxLayout(self.loading_overlay)
        loading_layout.setAlignment(Qt.AlignCenter)
        # 提示文字
        self.loading_label = QLabel(tr("combiner.loading"))
        self.loading_label.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: bold;
            background-color: transparent;
        """)
        loading_layout.addWidget(self.loading_label)
        # 取消按钮
        self.cancProcBtn = QPushButton(tr("button.cancel"), self)
        self.cancProcBtn.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: bold;
            border: 1px solid white;
            background-color: transparent;
        """)
        self.cancProcBtn.setFixedHeight(30)
        self.cancProcBtn.clicked.connect(self.cancelProcess)
        loading_layout.addWidget(self.cancProcBtn)

        # ****** 状态栏（对话框不使用状态栏，仅记录日志） ******
        self.updateStatusBarTips()

    def _init_notifier_from_config(self):
        config_path = GlobalConfig.CONFIG_FILE_PATH

        if not os.path.exists(config_path):
            return

        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')

        section = "Notification"
        if not config.has_section(section):
            return

        def _get(key, default=""):
            return config.get(section, key, fallback=default)

        def _get_bool(key, default=False):
            try:
                v = config.get(section, key, fallback="1" if default else "0")
                return v in ("1", "true", "True")
            except Exception:
                return default

        notify_system = _get_bool("notify_system", True)
        notify_email = _get_bool("notify_email", False)
        notify_wechat = _get_bool("notify_wechat", False)

        smtp_host = _get("smtp_host") or None
        smtp_port_text = _get("smtp_port")
        try:
            smtp_port = int(smtp_port_text) if smtp_port_text else None
        except ValueError:
            smtp_port = None
        smtp_user = _get("smtp_user") or None
        smtp_pass = _get("smtp_pass") or None
        smtp_from = _get("smtp_from") or None
        smtp_to_text = _get("smtp_to")
        smtp_to_list = [x.strip() for x in smtp_to_text.split(
            ",") if x.strip()] if smtp_to_text else None

        use_ssl = _get_bool("use_ssl", False)
        use_tls = _get_bool("use_tls", True)

        wechat_webhook = _get("wechat_webhook") or None
        wechat_mentions_text = _get("wechat_mentions")
        wechat_mentions = [x.strip() for x in wechat_mentions_text.split(
            ",") if x.strip()] if wechat_mentions_text else None

        self.notifier = Notifier(
            enable_system=notify_system,
            enable_email=notify_email,
            enable_wechat=notify_wechat,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_pass=smtp_pass,
            smtp_from=smtp_from,
            smtp_to=smtp_to_list,
            use_ssl=use_ssl,
            use_tls=use_tls,
            wechat_webhook=wechat_webhook,
            wechat_mentions=wechat_mentions,
        )

    def ffmpegPathChanged(self):
        folder = self.ffmpegPath.text()

        if platform.system() == "Darwin" or platform.system() == "Linux":
            if os.path.exists(os.path.join(folder, "ffmpeg")):
                pass
            else:
                QMessageBox.question(
                    self,
                    tr("dialog.tip.title"),
                    tr(
                        "combiner.ffmpeg.not_found",
                        folder=folder,
                        default=self.get_default_ffmpeg_path(),
                    ),
                    QMessageBox.Yes,
                )
                self.ffmpegPath.setText(self.get_default_ffmpeg_path())
                self.save_config()
        elif platform.system() == "Windows":
            if os.path.exists(os.path.join(folder, "ffmpeg.exe")):
                pass
            else:
                QMessageBox.question(
                    self,
                    tr("dialog.tip.title"),
                    tr(
                        "combiner.ffmpeg.not_found",
                        folder=folder,
                        default=self.get_default_ffmpeg_path(),
                    ),
                    QMessageBox.Yes,
                )
                self.ffmpegPath.setText(self.get_default_ffmpeg_path())
                self.save_config()

        self.addFFmpegEnvPath()
        self.updateStatusBarTips()

    def updateStatusBarTips(self):
        # 对话框中不显示状态栏，仅在日志中记录 FFmpeg 可用状态
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            status = tr("combiner.status.ffmpeg_available")
        else:
            status = tr("combiner.status.ffmpeg_unavailable")
        detail = ffmpeg_path if ffmpeg_path else "FFmpeg not installed or not in PATH"
        ffmpegtips = tr("combiner.status.ffmpeg_detail", status=status, detail=detail)
        self.glogger.info(ffmpegtips)

    def addFFmpegEnvPath(self):
        # 添加FFmpeg路径的工作环境变量
        FFMPEG_HOME = self.ffmpegPath.text()
        PATH = os.environ['PATH']
        os.environ['PATH'] = f'{FFMPEG_HOME}:{PATH}'

        # NewPATH = os.environ['PATH']
        # self.glogger.info(f"New PATH: {NewPATH}")

    def setMainView(self, zh_view):
        view_map = {
            tr("player.view.front"): 'front',
            tr("player.view.back"): 'back',
            tr("player.view.left"): 'left',
            tr("player.view.right"): 'right',
        }
        view = view_map.get(zh_view, 'front')
        self.main_view = view
        self.save_config()

    def is_tesla_cam_video_folder(self, folder_path):
        """判断文件夹下文件是否符合特斯拉行车记录仪视频文件规范"""
        files = os.listdir(folder_path)
        pattern = re.compile(
            r"(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})-(front|back|left_repeater|right_repeater)\.mp4")
        group_dict = {}
        for f in files:
            match = pattern.match(f)
            if match:
                timestamp, view = match.groups()
                view_map = {
                    'front': 'front',
                    'back': 'back',
                    'left_repeater': 'left',
                    'right_repeater': 'right'
                }
                view_key = view_map[view]
                group_dict.setdefault(timestamp, {})[
                    view_key] = os.path.join(folder_path, f)
        # 按时间戳排序并过滤空组
        group_dict = {k: v for k, v in sorted(
            group_dict.items()) if len(v) == 4}
        groups = [group for ts, group in sorted(
            group_dict.items()) if len(group) == 4]
        return True if len(groups) > 0 else False

    def browseFolder(self, foldertype):
        # 设置默认路径
        if foldertype == "inputType":
            if self.inputFolder.text() != "" and os.path.exists(self.inputFolder.text()):
                folder = QFileDialog.getExistingDirectory(
                    self, tr("filedialog.select_folder"), self.inputFolder.text())
            else:
                folder = QFileDialog.getExistingDirectory(
                    self, tr("filedialog.select_folder"), os.path.expanduser('~'))
        elif foldertype == "outputType":
            if self.outputFolder.text() != "" and os.path.exists(self.outputFolder.text()):
                folder = QFileDialog.getExistingDirectory(
                    self, tr("filedialog.select_folder"), self.outputFolder.text())
            else:
                folder = QFileDialog.getExistingDirectory(
                    self, "选择文件夹", os.path.expanduser('~'))
        elif foldertype == "ffmpegType":
            if self.ffmpegPath.text() != "" and os.path.exists(self.ffmpegPath.text()):
                folder = QFileDialog.getExistingDirectory(
                    self, tr("filedialog.select_folder"), self.ffmpegPath.text())
            else:
                folder = QFileDialog.getExistingDirectory(
                    self, "选择文件夹", os.path.expanduser('~'))
        else:
            folder = QFileDialog.getExistingDirectory(
                self, tr("filedialog.select_folder"), os.path.expanduser('~'))

        if folder:
            if foldertype == "inputType":
                if not self.is_tesla_cam_video_folder(folder):
                    QMessageBox.question(
                        self,
                        tr("dialog.tip.title"),
                        tr("combiner.ffmpeg.invalid_tesla_folder", folder=folder),
                        QMessageBox.Yes,
                    )
                else:
                    self.inputFolder.setText(folder)
                    self.outputFolder.setText(os.path.join(folder, "temps"))
                    self.save_config()
            elif foldertype == "outputType":
                self.outputFolder.setText(folder)
                self.save_config()
            elif foldertype == "ffmpegType":
                if platform.system() == "Darwin":
                    if os.path.exists(os.path.join(folder, "ffmpeg")):
                        self.ffmpegPath.setText(folder)
                        self.save_config()
                    else:
                        QMessageBox.question(
                            self,
                            tr("dialog.tip.title"),
                            tr("combiner.ffmpeg.not_found", folder=folder, default=self.get_default_ffmpeg_path()),
                            QMessageBox.Yes,
                        )
                elif platform.system() == "Windows":
                    if os.path.exists(os.path.join(folder, "ffmpeg.exe")):
                        self.ffmpegPath.setText(folder)
                        self.save_config()
                    else:
                        QMessageBox.question(
                            self, '提示', f'{folder} 路径下不存在 FFmpeg', QMessageBox.Yes)
                elif platform.system() == "Linux":
                    self.ffmpegPath.setText(folder)
                    self.save_config()
                else:
                    self.ffmpegPath.setText(folder)
                    self.save_config()
            else:
                self.glogger.info(f"未知路径设置: {foldertype}")
        else:
            self.glogger.info("未选择文件夹")

    def resetFFmpegPath(self):
        if self.init_default_ffmpeg_path:
            self.ffmpegPath.setText(self.init_default_ffmpeg_path)
            self.save_config()
        else:
            QMessageBox.question(
                self,
                tr("dialog.tip.title"),
                tr("combiner.ffmpeg.default_missing"),
                QMessageBox.Yes,
            )

    def get_default_ffmpeg_path(self):
        # 设置初始默认路径（使用了 := 海象运算符和三元表达式来简化）
        ffmpeg_path = shutil.which("ffmpeg")
        default_path = '/usr/local/bin' if sys.platform.startswith(
            'darwin') and os.path.exists('/usr/local/bin/ffmpeg') else ""

        if sys.platform.startswith('win'):
            return ffmpeg_path[:-10] if ffmpeg_path else default_path
        else:
            return ffmpeg_path[:-6] if ffmpeg_path else default_path

    def openAudioFile(self):
        """Open a mp3 audio file"""
        if self.audioFilePath.text() != "" and os.path.exists(self.audioFilePath.text()):
            # 路径已设置并存在，则默认打开设置的路径
            filename = QFileDialog.getOpenFileName(
                self,
                tr("filedialog.select_mp3"),
                self.audioFilePath.text(),
                tr("filedialog.filter_mp3"),
            )
        else:
            filename = QFileDialog.getOpenFileName(
                self,
                tr("filedialog.select_mp3"),
                os.path.expanduser('~'),
                tr("filedialog.filter_mp3"),
            )

        if not filename or not filename[0]:
            return

        self.audioFilePath.setText(filename[0])
        self.save_config()

    def openInputPath(self):
        self.openFolderOrFile(self.inputFolder.text())

    def play(self):
        if not os.path.exists(self.inputFolder.text()):
            QMessageBox.question(
                self, '提示', '输入视频路径不存在', QMessageBox.Yes)
            return

        try:
            # 延迟导入主程序窗口类，避免与 TeslaCamPlayerWidget 的集成产生循环依赖
            from MainWindow import TeslaCamPlayer
        except Exception as e:
            self.glogger.error(f"导入 TeslaCamPlayer 失败: {e}")
            QMessageBox.question(
                self, '提示', '无法打开 TeslaCam Player 主窗口', QMessageBox.Yes)
            return

        try:
            # 当前主程序的 TeslaCamPlayer 构造函数只接受可选的父窗口参数
            self.TeslaCamPlayer = TeslaCamPlayer(self)
            self.TeslaCamPlayer.show()
        except Exception as e:
            self.glogger.error(f"创建 TeslaCamPlayer 窗口失败: {e}")
            QMessageBox.question(
                self, '提示', '创建 TeslaCam Player 窗口失败', QMessageBox.Yes)

    def openAudioPath(self):
        self.openFolderOrFile(self.audioFilePath.text())

    def openOutputPath(self):
        self.openFolderOrFile(self.outputFolder.text())

    def openFolderOrFile(self, folder_path):
        # 检查文件夹是否存在
        if not os.path.exists(folder_path):
            # 判断是文件夹路径还是文件路径
            if os.path.isfile(folder_path):
                QMessageBox.question(
                    self, '提示', '文件不存在', QMessageBox.Yes)
            else:
                QMessageBox.question(
                    self, '提示', '文件夹不存在', QMessageBox.Yes)
            return

        try:
            # Windows 系统
            if os.name == 'nt':
                os.startfile(folder_path)
            # MacOS 系统
            elif os.name == 'posix':
                os.system(f'open "{folder_path}"')
            # Linux 系统
            else:
                os.system(f'xdg-open "{folder_path}"')
        except Exception as e:
            self.glogger.info(f"打开文件夹失败: {e}")

    def resourcePath(self, relative_path):
        """获取资源文件的绝对路径"""
        # 规范化路径
        relative_path = Path(relative_path)
        if hasattr(sys, '_MEIPASS') or getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, relative_path)

        return os.path.join(self.current_abspath, relative_path)

    def remove(self, folder_path):
        """ 删除文件夹下文件夹及文件 """
        try:
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    self.glogger.error(f"删除 {file_path} 时出错: {e}")

            # 如果需要，也可以删除父文件夹本身
            # os.rmdir(folder_path)

            self.glogger.info(f"成功清空文件夹: {folder_path}")
        except Exception as e:
            self.glogger.error(f"处理文件夹时出错: {e}")

    def tripleSpeedChanged(self):
        self.save_config()

    def amapApiKeyChanged(self):
        self.save_config()

    def finishProcess(self, message):
        self.loading_overlay.hide()

        if message == "fail":
            if self.notifier:
                try:
                    self.notifier.notify(
                        "TeslaCam 合成导出失败", "合成导出处理失败，请检查日志和配置。")
                except Exception:
                    self.glogger.error("通知发送失败", exc_info=True)
            QMessageBox.question(
                self, '提示', '处理失败', QMessageBox.Yes)
        elif message == "stop":
            if self.notifier:
                try:
                    self.notifier.notify("TeslaCam 合成导出已停止", "合成导出任务已被用户停止。")
                except Exception:
                    self.glogger.error("通知发送失败", exc_info=True)
            QMessageBox.question(
                self, '提示', '处理已停止', QMessageBox.Yes)
        else:
            if self.notifier:
                try:
                    self.notifier.notify("TeslaCam 合成导出完成", "合成导出已成功完成。")
                except Exception:
                    self.glogger.error("通知发送失败", exc_info=True)
            # self.glogger.info(f"处理完成: {message}")
            QMessageBox.question(
                self, '提示', '处理完成', QMessageBox.Yes)

    def updateProcessProgress(self, progress):
        self.procProgBar.setValue(progress)
        self.glogger.info(f"处理进度: {progress}%")

    def startProcess(self):
        # 输入视频为空和不存在判断
        if not self.inputFolder.text():
            QMessageBox.question(
                self, '提示', '输入视频路径不能为空', QMessageBox.Yes)
            return
        else:
            if not os.path.exists(self.inputFolder.text()):
                QMessageBox.question(
                    self, '提示', '输入视频路径不存在', QMessageBox.Yes)
                return
        # 输入音频为空、不存在和格式判断
        if not self.audioFilePath.text():
            QMessageBox.question(
                self, '提示', '输入音频不能为空', QMessageBox.Yes)
            return
        else:
            if not os.path.exists(self.audioFilePath.text()) or not os.path.isfile(self.audioFilePath.text()):
                QMessageBox.question(
                    self, '提示', '输入音频不存在', QMessageBox.Yes)
                return
            else:
                if not self.audioFilePath.text().endswith(".mp3"):
                    QMessageBox.question(
                        self, '提示', '输入音频格式不正确', QMessageBox.Yes)
                    return

        if os.path.exists(self.outputFolder.text()):
            reply = QMessageBox.question(self, '提示',
                                         f'是否删除 {self.outputFolder.text()} 文件夹下的内容?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.remove(self.outputFolder.text())

        self.core_worker = CoreWorker(self, self.signals,
                                      self.inputFolder.text(), self.audioFilePath.text(),
                                      self.outputFolder.text(), self.tripleSpeed.value(),
                                      self.amapApiKey.text(), self.main_view)
        self.core_worker.start()

        self.procProgBar.setValue(0)
        self.loading_overlay.show()

    def cancelProcess(self):
        reply = QMessageBox.question(
            self, '提示', '是否停止处理', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.core_worker.stop()

    def save_config(self):
        try:
            # 配置文件保存路径
            config_path = GlobalConfig.CONFIG_FILE_PATH

            if os.path.exists(config_path):
                # 如果配置文件存在就读取
                config = configparser.ConfigParser()
                config.read(config_path, encoding='utf-8')

                config.set("Settings", "inputPath",
                           f"{self.inputFolder.text()}")
                config.set("Settings", "audioFilePath",
                           f"{self.audioFilePath.text()}")
                config.set("Settings", "outputPath",
                           f"{self.outputFolder.text()}")
                config.set("Settings", "ffmpegPath",
                           f"{self.ffmpegPath.text()}")
                config.set("Settings", "tripleSpeed",
                           f"{self.tripleSpeed.value()}")
                config.set("Settings", "amapApiKey",
                           f"{self.amapApiKey.text()}")
                config.set("Settings", "mainView",
                           f"{self.mainViewBox.currentText()}")

                config.write(open(config_path, "w", encoding="utf-8"))
            else:
                # 如果没有配置文件就创建
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write("[Settings]\n")
                    f.write(f"inputPath = {self.inputFolder.text()}\n")
                    f.write(f"audioFilePath = {self.audioFilePath.text()}\n")
                    f.write(f"outputPath = {self.outputFolder.text()}\n")
                    f.write(f"ffmpegPath = {self.ffmpegPath.text()}\n")
                    f.write(f"tripleSpeed = {self.tripleSpeed.value()}\n")
                    f.write(f"amapApiKey = {self.amapApiKey.text()}\n")
                    f.write(f"mainView = {self.mainViewBox.currentText()}\n")
        except Exception as e:
            self.glogger.error(f"配置保存异常: {e}")

    def read_config(self):
        # 配置文件保存路径
        config_path = GlobalConfig.CONFIG_FILE_PATH

        # 如果配置文件存在就读取
        if os.path.exists(config_path):
            config = configparser.ConfigParser()
            config.read(config_path, encoding='utf-8')

            try:
                self.inputFolder.setText(config.get("Settings", "inputPath"))
                self.audioFilePath.setText(
                    config.get("Settings", "audioFilePath"))
                self.outputFolder.setText(config.get("Settings", "outputPath"))
                self.ffmpegPath.setText(config.get("Settings", "ffmpegPath"))
                self.tripleSpeed.setValue(
                    float(config.get("Settings", "tripleSpeed")))
                self.amapApiKey.setText(config.get("Settings", "amapApiKey"))
                self.mainViewBox.setCurrentText(
                    config.get("Settings", "mainView"))
            except configparser.NoOptionError as err:
                self.glogger.error(f'配置文件缺少选项: {err}')
            except Exception as ex:
                self.glogger.error(f'配置读取异常: {ex}')

    def resizeEvent(self, event):
        # 窗口大小改变时调整覆盖层大小
        self.loading_overlay.resize(self.size())
        super().resizeEvent(event)

    def keyPressEvent(self, event):
        # ESC 键触发与点击关闭按钮相同的逻辑
        if event.key() == Qt.Key_Escape:
            # 交给 closeEvent 统一处理确认和停止任务
            self.close()
            # 不再交给父类处理，避免重复行为
            return

        return super().keyPressEvent(event)

    def closeEvent(self, event):
        # 如果有正在运行的处理任务，关闭前进行确认
        if self.core_worker is not None and self.core_worker.isRunning():
            reply = QMessageBox.question(
                self,
                '提示',
                '当前视频正在处理，是否停止并关闭窗口？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                try:
                    self.core_worker.stop()
                except Exception as e:
                    self.glogger.error(f"停止处理任务失败: {e}")

                self.loading_overlay.hide()
                event.accept()
            else:
                event.ignore()
                return

        super().closeEvent(event)
