# -*- coding: utf-8 -*-

# 标准库
import os
import re
import logging
import platform

# 三方库
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import qtawesome as qta
import vlc

# 自研库
# try:
#     import GlobalConfig
# except Exception:
#     GlobalConfig = None
# from utils import logger as build_logger


class VideoContextMenu(QMenu):
    """视频播放区域的右键菜单"""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent_widget = parent
        # 设置菜单样式，确保图标尺寸一致
        self.setStyleSheet("""
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
                min-height: 20px;
            }
            QMenu::item:selected {
                background: #e6f7ff;
                color: #1890ff;
            }
            QMenu::item:hover {
                background: #f5f5f5;
            }
            QMenu::icon {
                width: 16px;
                height: 16px;
            }
        """)
        # 存储菜单动作的引用
        self.speed_actions = {}
        self.view_actions = {}
        self.setup_menu()

    def setup_menu(self):
        """设置菜单项"""
        # 播放/暂停
        self.play_pause_action = QAction("播放", self)
        self.play_pause_action.triggered.connect(self.toggle_play_pause)
        # 设置统一的图标尺寸
        self.play_pause_action.setIcon(qta.icon('mdi.play', color='#1890ff'))
        self.addAction(self.play_pause_action)

        # 停止
        stop_action = QAction("停止", self)
        stop_action.triggered.connect(self.parent_widget.stop_all)
        # 设置统一的图标尺寸
        stop_action.setIcon(qta.icon('mdi.stop', color='#1890ff'))
        self.addAction(stop_action)

        self.addSeparator()

        # 播放倍数子菜单
        speed_menu = self.addMenu("倍数")
        speed_menu.setIcon(qta.icon('mdi.speedometer', color='#1890ff'))
        speeds = [
            ("0.5x", 0.5),
            ("1x", 1),
            ("2x", 2),
            ("4x", 4),
            ("8x", 8),
            ("10x", 10)
        ]
        for speed_text, speed_value in speeds:
            action = QAction(speed_text, self)
            # 使用更明确的方法连接信号
            action.triggered.connect(
                lambda checked, v=speed_value: self.parent_widget.set_rate_all(v))
            # 保存动作引用
            self.speed_actions[speed_value] = action
            # 为当前倍速添加选中标记
            if speed_value == 1.0:  # 默认1x倍速
                action.setIcon(qta.icon('mdi.check', color='#52c41a'))
            speed_menu.addAction(action)

        self.addSeparator()

        # 主视角切换子菜单
        view_menu = self.addMenu("主视角")
        view_menu.setIcon(qta.icon('mdi.view-dashboard', color='#1890ff'))
        views = [("前", "front"), ("后", "back"), ("左", "left"), ("右", "right")]
        for view_text, view_key in views:
            action = QAction(view_text, self)
            action.triggered.connect(
                lambda checked, v=view_text: self.parent_widget.set_main_view(v))
            # 保存动作引用
            self.view_actions[view_key] = action
            # 为当前主视角添加选中标记
            if view_key == "front":  # 默认前视角
                action.setIcon(qta.icon('mdi.check', color='#52c41a'))
            view_menu.addAction(action)

        self.addSeparator()

        # 合成导出
        combine_export_action = QAction("合成导出", self)
        combine_export_action.setIcon(
            qta.icon('mdi.movie-edit', color='#1890ff'))
        combine_export_action.triggered.connect(self.show_combine_export)
        self.addAction(combine_export_action)

    # def show_export_dialog(self):
    #     """显示导出配置对话框"""
    #     self.parent_widget.show_export_dialog()

    def show_combine_export(self):
        """显示片段合成导出窗口"""
        self.parent_widget.show_combine_export()

    def toggle_play_pause(self):
        """切换播放/暂停状态"""
        self.parent_widget.play_pause_all()

    def update_play_pause_text(self):
        """更新播放/暂停按钮文字和图标"""
        # 检查是否有播放器正在播放
        any_playing = any(player.get_state() == vlc.State.Playing
                          for player in self.parent_widget.players.values())

        if any_playing:
            self.play_pause_action.setText("暂停")
            self.play_pause_action.setIcon(
                qta.icon('mdi.pause', color='#1890ff'))
        else:
            self.play_pause_action.setText("播放")
            self.play_pause_action.setIcon(
                qta.icon('mdi.play', color='#1890ff'))

    def update_speed_selection(self, current_speed):
        """更新倍数选择的勾选状态"""
        self.parent_widget.glogger.info(f"更新右键菜单倍数选择: {current_speed}")

        # 清除所有倍数动作的勾选图标
        for action in self.speed_actions.values():
            action.setIcon(QIcon())  # 清空图标

        # 为当前倍数添加勾选图标
        if current_speed in self.speed_actions:
            self.speed_actions[current_speed].setIcon(
                qta.icon('mdi.check', color='#52c41a'))
            self.parent_widget.glogger.info(f"已为倍数 {current_speed} 添加勾选图标")
        else:
            self.parent_widget.glogger.warning(f"未找到倍数 {current_speed} 对应的动作")

    def update_view_selection(self, current_view):
        """更新视角选择的勾选状态"""
        # 清除所有视角动作的勾选图标
        for action in self.view_actions.values():
            action.setIcon(QIcon())  # 清空图标

        # 为当前视角添加勾选图标
        if current_view in self.view_actions:
            self.view_actions[current_view].setIcon(
                qta.icon('mdi.check', color='#52c41a'))


class TeslaCamPlayerWidget(QWidget):
    folderChanged = pyqtSignal(str)  # 自定义信号
    warningEmitted = pyqtSignal(str)
    infoEmitted = pyqtSignal(str)

    def __init__(self, folder_path, logger_instance=None, enable_dialogs=True, enable_file_dialog=True, log_dir=None):
        super().__init__()

        # 运行时配置
        self.enable_dialogs = enable_dialogs
        self.enable_file_dialog = enable_file_dialog

        # 初始化日志（支持注入）
        if logger_instance is not None:
            self.glogger = logger_instance
        else:
            # # 初始化日志（使用指定目录/GlobalConfig，最后降级为控制台）
            # try:
            #     if log_dir is not None:
            #         self.glogger = build_logger(
            #             log_dir, False, f"TeslaCamPlayerWidget-{id(self)}")
            #     elif GlobalConfig and hasattr(GlobalConfig, 'LOG_DIR'):
            #         self.glogger = build_logger(
            #             GlobalConfig.LOG_DIR, False, f"TeslaCamPlayerWidget-{id(self)}")
            #     else:
            #         raise RuntimeError(
            #             'No log_dir provided and GlobalConfig missing')
            # except Exception:
            #     fallback_logger = logging.getLogger(
            #         f"TeslaCamPlayerWidget-{id(self)}")
            #     if not fallback_logger.handlers:
            #         fallback_logger.setLevel(logging.INFO)
            #         ch = logging.StreamHandler()
            #         ch.setFormatter(logging.Formatter(
            #             fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%Y/%m/%d %X"))
            #         fallback_logger.addHandler(ch)
            #     self.glogger = fallback_logger

            self.glogger = logging.getLogger("TeslaCamPlayerWidget")

        self.instances = {k: vlc.Instance()
                          for k in ['front', 'back', 'left', 'right']}
        self.players = {k: self.instances[k].media_player_new() for k in [
            'front', 'back', 'left', 'right']}

        self.current_main_view = 'front'
        self.current_index = 0
        # 标记是否为用户点击"停止"导致的停止，用于下一次播放从第一个片段开始
        self.stopped_by_user = False

        # 当前播放倍数和视角状态跟踪
        self.current_speed = 1.0  # 默认1x倍速
        self.current_view = 'front'  # 默认前视角

        self.inputFolderPath = folder_path

        self.video_groups = None
        self.video_group_dict = None

        # 创建右键菜单
        self.context_menu = VideoContextMenu(self)

        self.create_ui()

        # 初始化右键菜单状态
        self.context_menu.update_speed_selection(self.current_speed)
        self.context_menu.update_view_selection(self.current_view)

        if self.inputFolderPath != "" and os.path.exists(self.inputFolderPath):
            self.glogger.info(f"初始化加载目录: {self.inputFolderPath}")
            self.load_all(self.inputFolderPath)
        else:
            self.glogger.info("初始未提供有效目录，等待用户选择")

    def create_ui(self):
        """Set up the user interface, signals & slots"""

        # Ant Design 风格（仅样式，不改布局）
        # 主题蓝 #1890ff、悬停 #40a9ff、选中浅蓝背景 #e6f7ff、边框 #d9d9d9
        self.setStyleSheet("""
            QWidget { color: #262626; font-family: 'Microsoft YaHei','PingFang SC','Helvetica Neue',Arial; }
            QPushButton {
                background: #1890ff; color: #ffffff; border: 1px solid #1890ff;
                border-radius: 4px; padding: 6px 12px; font-weight: 500;
            }
            QPushButton:hover { background: #40a9ff; border-color: #40a9ff; }
            QPushButton:pressed { background: #096dd9; border-color: #096dd9; }
            QPushButton:disabled { background: #f5f5f5; color: #bfbfbf; border-color: #d9d9d9; }

            QListWidget { background: #ffffff; border: 1px solid #d9d9d9; border-radius: 4px; }
            QListWidget::item { padding: 6px 10px; margin: 2px; border-radius: 3px; }
            QListWidget::item:selected { background: #e6f7ff; color: #1890ff; }
            QListWidget::item:hover { background: #fafafa; }

            QSlider::groove:horizontal { height: 4px; background: #f0f0f0; border-radius: 2px; }
            QSlider::handle:horizontal { background: #1890ff; width: 16px; height: 16px; border-radius: 8px; margin: -6px 0; }
            QSlider::handle:horizontal:hover { background: #40a9ff; }

            QComboBox { background: #ffffff; border: 1px solid #d9d9d9; border-radius: 4px; padding: 4px 8px; }
            QComboBox:hover { border-color: #40a9ff; }
            QComboBox QAbstractItemView { border: 1px solid #d9d9d9; selection-background-color: #e6f7ff; }

            QLabel { color: #262626; }
        """)

        self.widgets = {k: QLabel(self)
                        for k in ['front', 'back', 'left', 'right']}
        for widget in self.widgets.values():
            widget.setStyleSheet(
                "background-color: #000000; border: 1px solid #1f1f1f; border-radius: 4px;")
            widget.setScaledContents(True)
            # 启用右键菜单
            widget.setContextMenuPolicy(Qt.CustomContextMenu)
            widget.customContextMenuRequested.connect(self.show_context_menu)

        # 左侧布局
        left_layout = QVBoxLayout()
        # 打开文件夹按钮
        open_folder_button = QPushButton("打开文件夹", self)
        open_folder_button.clicked.connect(
            lambda: self.browse_folder("inputType"))
        left_layout.addWidget(open_folder_button)

        # 左侧列表
        self.time_point_list = QListWidget()
        self.time_point_list.setMaximumWidth(200)
        self.time_point_list.itemClicked.connect(self.load_time_point_group)
        left_layout.addWidget(self.time_point_list)

        # 右侧播放器
        self.video_layout = QGridLayout()
        self.control_layout = self.build_controls()

        player_layout = QVBoxLayout()
        player_layout.addLayout(self.video_layout)
        player_layout.addLayout(self.control_layout)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout)
        main_layout.addLayout(player_layout)

        self.setLayout(main_layout)

        self.setup_video_widgets()

        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(1000)

    def get_all_video_groups(self, folder_path):
        """
        特斯拉行车记录仪保存到U盘中的视频文件规范:
        TeslaCam
            |--SavedClips
                |--2025-04-06_17-42-25
                    |--2025-04-06_17-32-11-back.mp4
                    |--2025-04-06_17-32-11-front.mp4
                    |--2025-04-06_17-32-11-left_repeater.mp4
                    |--2025-04-06_17-32-11-right_repeater.mp4
                    |--2025-04-06_17-33-11-back.mp4
                    |--...
        """
        self.glogger.info(f"扫描目录获取视频分组: {folder_path}")
        try:
            files = os.listdir(folder_path)
        except Exception as ex:
            self.glogger.error(f"目录读取失败: {folder_path}, 原因: {ex}")
            return [], {}
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

        self.glogger.info(f"共匹配到时间段: {len(groups)} 组")

        return groups, group_dict

    def setup_video_widgets(self):
        for i in reversed(range(self.video_layout.count())):
            self.video_layout.itemAt(i).widget().setParent(None)

        # 主视角位置及大小
        self.video_layout.addWidget(
            self.widgets[self.current_main_view], 0, 0, 4, 4)

        # 非主视角位置及大小
        positions = {
            'front': (0, 0, 1, 1),    # 左上角
            'back': (0, 3, 1, 1),     # 右上角
            'left': (3, 0, 1, 1),     # 左下角
            'right': (3, 3, 1, 1),    # 右下角
        }

        for view in ['front', 'back', 'left', 'right']:
            if view == self.current_main_view:
                # 解决应用刚启动时，先单击主视角（前），然后切换到其他视角，
                # 再次单击前视角小窗无法将前视角切换为主视角问题
                self.widgets[view].mousePressEvent = lambda e, v=view: self.swap_view(
                    v)
                continue

            pos = positions.get(view)
            if pos:
                self.video_layout.addWidget(self.widgets[view], *pos)
                self.widgets[view].mousePressEvent = lambda e, v=view: self.swap_view(
                    v)

    def swap_view(self, new_main):
        if new_main == self.current_main_view:
            return

        self.main_view_box.setCurrentText({
            'front': '前',
            'back': '后',
            'left': '左',
            'right': '右'
        }[new_main])

        self.glogger.info(f"切换主视角: {self.current_main_view} -> {new_main}")
        self.current_main_view = new_main
        self.setup_video_widgets()

    def load_video_group(self, group):
        for view, path in group.items():
            self.glogger.info(f"加载视频: view={view}, path={path}")
            media = self.instances[view].media_new(path)
            self.players[view].set_media(media)

            if platform.system() == "Linux":
                # for Linux using the X Server
                self.players[view].set_xwindow(
                    int(self.widgets[view].winId()))
            elif platform.system() == "Windows":
                # for Windows
                self.players[view].set_hwnd(
                    int(self.widgets[view].winId()))
            elif platform.system() == "Darwin":
                # for MacOS
                self.players[view].set_nsobject(
                    int(self.widgets[view].winId()))

            # 解决 Windows 版本单击视角小窗无法切换主视角的问题，同时貌似也解决了
            # 因 [0000019b3c799b80] direct3d11 vout display error: SetThumbNailClip failed: 0x800706f4 报错而导致界面卡死的问题
            # https://github.com/oaubert/python-vlc/issues/290#issuecomment-2690386548
            self.players[view].video_set_key_input(False)
            self.players[view].video_set_mouse_input(False)

    def play_all(self):
        self.glogger.info("开始播放所有视角")
        for player in self.players.values():
            player.play()
        self.play_pause_all_btn.setText('暂停')
        # self.play_pause_all_btn.setIcon(self.pause_icon)
        self.play_pause_all_btn.setIcon(qta.icon('mdi.pause', color='#ffffff'))

    def pause_all(self):
        self.glogger.info("暂停所有视角")
        for player in self.players.values():
            player.pause()
        self.play_pause_all_btn.setText('播放')
        # self.play_pause_all_btn.setIcon(self.play_icon)
        self.play_pause_all_btn.setIcon(qta.icon('mdi.play', color='#ffffff'))

    def play_pause_all(self):
        # 若有任一播放器正在播放，则执行“暂停”
        any_playing = any(player.get_state() ==
                          vlc.State.Playing for player in self.players.values())

        if any_playing:
            self.glogger.info("检测到播放中，执行暂停")
            for player in self.players.values():
                player.pause()
            self.play_pause_all_btn.setText('播放')
            self.play_pause_all_btn.setIcon(
                qta.icon('mdi.play', color='#ffffff'))
            return

        # 如果是用户点击“停止”后的首次播放，则从第一个片段开始
        if self.stopped_by_user:
            self.glogger.info("停止后首次播放：重置到第一组并预加载")
            self.current_index = 0
            if self.video_groups and len(self.video_groups) > 0:
                self.load_video_group(self.video_groups[0])
                # 同步左侧列表选中到第一项
                if self.time_point_list.count() > 0:
                    self.time_point_list.setCurrentRow(0)
            # 清除标志，避免后续播放总是回到第一段
            self.stopped_by_user = False

        self.glogger.info("执行播放")
        for player in self.players.values():
            player.play()
        self.play_pause_all_btn.setText('暂停')
        self.play_pause_all_btn.setIcon(
            qta.icon('mdi.pause', color='#ffffff'))

    def stop_all(self):
        self.glogger.info("停止所有视角，并标记下次从第一段开始")
        for player in self.players.values():
            player.stop()
        self.play_pause_all_btn.setText('播放')
        # self.play_pause_all_btn.setIcon(self.play_icon)
        self.play_pause_all_btn.setIcon(
            qta.icon('mdi.play', color='#ffffff'))

        # 用户主动停止：标记以便下次播放从第一段开始
        self.stopped_by_user = True
        # 重置索引并预加载第一组（不自动播放）
        if self.video_groups and len(self.video_groups) > 0:
            self.current_index = 0
            self.load_video_group(self.video_groups[0])
            if self.time_point_list.count() > 0:
                self.time_point_list.setCurrentRow(0)

    def stop_only(self):
        """仅停止播放，不改变当前索引、不预加载第一组、不修改列表选中状态。"""
        self.glogger.info("仅停止播放（不改变索引与列表状态）")
        for player in self.players.values():
            player.stop()
        self.play_pause_all_btn.setText('播放')
        self.play_pause_all_btn.setIcon(
            qta.icon('mdi.play', color='#0288D1'))

    def set_rate_all(self, rate):
        self.glogger.info(f"设置播放倍速: {rate}x")
        for player in self.players.values():
            player.set_rate(rate)

        # 更新当前倍数状态
        self.current_speed = rate
        self.glogger.info(f"当前倍数状态已更新为: {self.current_speed}")

        # 同步更新底部下拉框
        speed_text = f"{rate}x"
        if hasattr(self, 'speed_box') and self.speed_box is not None:
            try:
                # 先尝试直接设置文本，不使用blockSignals
                self.speed_box.setCurrentText(speed_text)
                # 强制处理事件
                QApplication.processEvents()
                # 验证更新是否成功
                current_text = self.speed_box.currentText()
                if current_text == speed_text:
                    self.glogger.info(f"底部下拉框已更新为: {speed_text}")
                else:
                    self.glogger.warning(
                        f"底部下拉框更新失败: 期望 {speed_text}, 实际 {current_text}")
                    # 尝试使用索引方式
                    self.speed_box.blockSignals(True)
                    index = self.speed_box.findText(speed_text)
                    if index >= 0:
                        self.speed_box.setCurrentIndex(index)
                        self.speed_box.update()
                        QApplication.processEvents()
                        current_text = self.speed_box.currentText()
                        if current_text == speed_text:
                            self.glogger.info(
                                f"底部下拉框通过索引更新成功: {speed_text} (索引: {index})")
                        else:
                            self.glogger.error(
                                f"底部下拉框索引更新失败: 期望 {speed_text}, 实际 {current_text}")
                    else:
                        self.glogger.warning(f"未找到匹配的倍数选项: {speed_text}")
                    self.speed_box.blockSignals(False)
            except Exception as e:
                self.glogger.error(f"更新底部下拉框失败: {e}")
        else:
            self.glogger.warning(f"speed_box 不存在或为 None")

        # 同步更新右键菜单的勾选状态
        if hasattr(self, 'context_menu') and self.context_menu is not None:
            try:
                self.context_menu.update_speed_selection(rate)
                self.glogger.info(f"右键菜单勾选状态已更新为: {rate}")
            except Exception as e:
                self.glogger.error(f"更新右键菜单失败: {e}")
        else:
            self.glogger.warning(f"context_menu 不存在或为 None")

    def set_volume_all(self, volume):
        self.glogger.info(f"设置音量: {volume}")
        for player in self.players.values():
            player.audio_set_volume(volume)

    def seek_all(self, position):
        self.glogger.info(f"跳转进度: {position:.3f}")
        for player in self.players.values():
            player.set_position(position)

    def set_main_view(self, zh_view):
        view = {
            '前': 'front',
            '后': 'back',
            '左': 'left',
            '右': 'right'
        }[zh_view]

        self.glogger.info(f"设置主视角: {zh_view} -> {view}")
        self.current_main_view = view
        self.current_view = view
        self.setup_video_widgets()

        # 同步更新底部下拉框
        if hasattr(self, 'main_view_box'):
            self.main_view_box.blockSignals(True)
            self.main_view_box.setCurrentText(zh_view)
            self.main_view_box.blockSignals(False)

        # 同步更新右键菜单的勾选状态
        if hasattr(self, 'context_menu'):
            self.context_menu.update_view_selection(view)

    def update_ui(self):
        # 自动下一组播放
        if all(player.get_state() == vlc.State.Ended for player in self.players.values()):
            self.current_index += 1
            if self.current_index >= len(self.video_groups):
                self.current_index = 0

            self.glogger.info(f"自动切换到下一组: index={self.current_index}")
            self.load_video_group(self.video_groups[self.current_index])
            self.play_all()
            self.time_point_list.setCurrentRow(self.current_index)

        # 更新进度条
        pos = self.players['front'].get_position()
        self.progress_slider.blockSignals(True)
        self.progress_slider.setValue(int(pos * 1000))
        self.progress_slider.blockSignals(False)

    def build_controls(self):
        layout = QHBoxLayout()

        # play_btn = QPushButton("▶ 播放")
        # play_btn.clicked.connect(self.play_all)
        # pause_btn = QPushButton("⏸ 暂停")
        # pause_btn.clicked.connect(self.pause_all)

        self.play_pause_all_btn = QPushButton("播放")
        self.play_pause_all_btn.clicked.connect(self.play_pause_all)
        self.play_pause_all_btn.setToolTip("播放/暂停")
        self.play_pause_all_btn.setIconSize(QSize(18, 18))
        # self.play_pause_all_btn.setIcon(self.play_icon)
        self.play_pause_all_btn.setIcon(qta.icon('mdi.play', color='#ffffff'))

        # stop_btn = QPushButton("⏹ 停止")
        stop_btn = QPushButton("停止")
        stop_btn.clicked.connect(self.stop_all)
        stop_btn.setToolTip("停止")
        stop_btn.setIconSize(QSize(18, 18))
        # stop_btn.setIcon(self.stop_icon)
        stop_btn.setIcon(qta.icon('mdi.stop', color='#ffffff'))

        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.sliderMoved.connect(
            lambda val: self.seek_all(val / 1000.0))

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMaximumWidth(120)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(self.set_volume_all)

        self.speed_box = QComboBox()
        self.speed_box.setPlaceholderText("倍数")
        self.speed_box.setToolTip("倍数")
        self.speed_box.addItems(["0.5x", "1x", "2x", "4x", "8x", "10x"])
        self.speed_box.setMinimumWidth(100)
        self.speed_box.setCurrentText("1x")
        self.speed_box.currentTextChanged.connect(
            lambda text: self.set_rate_all(float(text[:-1])))

        self.main_view_box = QComboBox()
        self.main_view_box.setPlaceholderText("主视角")
        self.main_view_box.setToolTip("主视角")
        self.main_view_box.addItems(["前", "后", "左", "右"])
        self.main_view_box.setMinimumWidth(100)
        self.main_view_box.setCurrentText("前")
        self.main_view_box.currentTextChanged.connect(
            lambda text: self.set_main_view(text))

        # layout.addWidget(play_btn)
        # layout.addWidget(pause_btn)
        layout.addWidget(self.play_pause_all_btn)
        layout.addWidget(stop_btn)
        layout.addWidget(QLabel("进度"))
        layout.addWidget(self.progress_slider)
        layout.addWidget(QLabel("音量"))
        layout.addWidget(self.volume_slider)
        layout.addWidget(self.speed_box)
        layout.addWidget(self.main_view_box)

        return layout

    def load_time_point_group(self, item):
        item_text = item.text()
        self.glogger.info(f"选择时间段: {item_text}")
        # 仅停止播放，不触发回到第一项的行为
        self.stop_only()
        video_group = self.video_group_dict[item_text]
        self.load_video_group(video_group)
        self.current_index = self.video_groups.index(video_group)
        self.play_all()

    def browse_folder(self, foldertype):
        if not self.enable_file_dialog:
            self.glogger.info("文件对话框已禁用：browse_folder 调用被忽略")
            self.infoEmitted.emit("文件对话框已禁用")
            return
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
            self.glogger.info(f"用户选择目录: {folder}")
            if foldertype == "inputType":
                self.inputFolderPath = folder
                # 触发事件
                self.folderChanged.emit(folder)
            else:
                self.glogger.info(f"未知路径设置: {foldertype}")
        else:
            self.glogger.info("未选择文件夹")

        if folder and os.path.exists(folder):
            self.load_all(folder)

    def load_all(self, folder):
        self.inputFolderPath = folder

        self.glogger.info(f"加载目录: {folder}")
        self.stop_all()
        self.current_index = 0

        self.video_groups, self.video_group_dict = self.get_all_video_groups(
            folder)

        self.time_point_list.clear()

        if len(self.video_groups) == 0:
            self.glogger.warning("未找到符合特斯拉视频文件规范的文件")
            self.play_pause_all_btn.setDisabled(True)

            self.video_groups = [
                {'front': '', 'back': '', 'left': '', 'right': ''}]
            self.load_video_group(self.video_groups[0])

            if self.enable_dialogs:
                QMessageBox.question(
                    self, '提示', '未找到符合特斯拉行车记录仪视频文件规范的文件', QMessageBox.Yes)
            else:
                self.warningEmitted.emit('未找到符合特斯拉行车记录仪视频文件规范的文件')
            return
        else:
            self.glogger.info(f"加载到有效视频组数量: {len(self.video_groups)}")
            self.play_pause_all_btn.setDisabled(False)

        for display_name, group in self.video_group_dict.items():
            self.time_point_list.addItem(display_name)
        self.time_point_list.setCurrentRow(self.current_index)

        self.load_video_group(self.video_groups[self.current_index])
        # self.play_all()

    def is_vlc_installed(self):
        try:
            instance = vlc.Instance()
            instance.media_player_new()
            return True
        except Exception as e:
            return False

    def get_libvlc_version(self):
        return vlc.libvlc_get_version()

    def show_context_menu(self, position):
        """显示右键菜单"""
        self.glogger.info("显示视频播放区域右键菜单")
        # 更新播放/暂停按钮文字
        self.context_menu.update_play_pause_text()
        # 更新倍数和视角的勾选状态
        self.context_menu.update_speed_selection(self.current_speed)
        self.context_menu.update_view_selection(self.current_view)

        # 获取发送信号的widget（视频播放区域）
        sender_widget = self.sender()
        if sender_widget:
            # 将widget内的相对坐标转换为全局坐标
            global_pos = sender_widget.mapToGlobal(position)
        else:
            # 备用方案：使用当前widget的坐标
            global_pos = self.mapToGlobal(position)

        # 获取屏幕尺寸，确保菜单不会超出屏幕边界
        screen = QApplication.desktop().screenGeometry()
        menu_size = self.context_menu.sizeHint()

        # 调整菜单位置，确保完全显示在屏幕内
        if global_pos.x() + menu_size.width() > screen.width():
            global_pos.setX(screen.width() - menu_size.width() - 10)
        if global_pos.y() + menu_size.height() > screen.height():
            global_pos.setY(screen.height() - menu_size.height() - 10)

        # 确保位置不为负数
        global_pos.setX(max(10, global_pos.x()))
        global_pos.setY(max(10, global_pos.y()))

        # 显示菜单
        self.context_menu.exec_(global_pos)

    def show_combine_export(self):
        """打开 TeslaCam 片段合成导出窗口"""
        # 确保当前已选择有效的视频文件夹
        if not self.inputFolderPath or not os.path.exists(self.inputFolderPath):
            if self.enable_dialogs:
                QMessageBox.warning(self, "提示", "请先选择有效的视频文件夹")
            else:
                self.warningEmitted.emit("请先选择有效的视频文件夹")
            return

        try:
            from CamClipCombiner.CamClipCombinerWin import CamClipCombiner
        except Exception as e:
            self.glogger.error(f"导入合成导出窗体失败: {e}")
            if self.enable_dialogs:
                QMessageBox.critical(self, "错误", f"无法打开合成导出窗口:\n{e}")
            else:
                self.warningEmitted.emit("无法打开合成导出窗口")
            return

        try:
            # 仅创建一个实例，重复调用时激活已有窗口
            if not hasattr(self, "clip_combiner_win") or self.clip_combiner_win is None:
                self.clip_combiner_win = CamClipCombiner(self)

            # 传递当前输入目录
            self.clip_combiner_win.inputFolder.setText(self.inputFolderPath)

            # 默认输出到当前目录下 temps 子目录（若 combiner 已有配置则保持现有值）
            if self.clip_combiner_win.outputFolder.text().strip() == "" or \
                    not os.path.isabs(self.clip_combiner_win.outputFolder.text()):
                self.clip_combiner_win.outputFolder.setText(
                    os.path.join(self.inputFolderPath, "temps")
                )

            # 同步主视角（以当前播放主视角为准）
            view_map = {
                "front": "前",
                "back": "后",
                "left": "左",
                "right": "右",
            }
            zh_view = view_map.get(getattr(self, "current_view", "front"), "前")
            if hasattr(self.clip_combiner_win, "mainViewBox"):
                self.clip_combiner_win.mainViewBox.setCurrentText(zh_view)

            self.clip_combiner_win.show()
            self.clip_combiner_win.raise_()
            self.clip_combiner_win.activateWindow()

        except Exception as e:
            self.glogger.error(f"打开合成导出窗口失败: {e}")
            if self.enable_dialogs:
                QMessageBox.critical(self, "错误", f"打开合成导出窗口失败:\n{e}")
            else:
                self.warningEmitted.emit("打开合成导出窗口失败")

    def resizeEvent(self, event):
        # # 获取屏幕分辨率
        # screen = QDesktopWidget().screenGeometry()

        return super().resizeEvent(event)

    def closeEvent(self, event):
        for player in self.players.values():
            player.stop()
        for player in self.players.values():
            player.release()
        for instance in self.instances.values():
            instance.release()
        self.timer.stop()

        return super().closeEvent(event)

    # def show_export_dialog(self):
    #     """显示导出配置对话框"""
    #     if not hasattr(self, 'inputFolderPath') or not self.inputFolderPath:
    #         QMessageBox.warning(self, "提示", "请先选择视频文件夹")
    #         return

    #     # 获取当前设置
    #     current_speed = getattr(self, 'current_speed', 1.0)
    #     current_view = getattr(self, 'current_view', 'front')

    #     # 创建导出对话框
    #     from ExportDialog import ExportDialog
    #     self.export_dialog = ExportDialog(
    #         self,
    #         self.inputFolderPath,
    #         current_speed,
    #         current_view
    #     )

    #     # 连接信号
    #     self.export_dialog.export_requested.connect(self.start_export)
    #     self.export_dialog.export_cancelled.connect(self.cancel_export)

    #     # 显示对话框
    #     self.export_dialog.exec_()

    # def start_export(self, export_params):
    #     """开始导出"""
    #     try:
    #         # 创建信号对象
    #         from Signal import Signal
    #         signals = Signal()

    #         # 创建导出工作线程
    #         from ExportWorker import ExportWorker
    #         self.export_worker = ExportWorker(
    #             self,
    #             signals,
    #             export_params['input_folder'],
    #             export_params['audio_file'],
    #             export_params['output_folder'],
    #             export_params['speed'],
    #             export_params['amap_api_key'],
    #             export_params['main_view']
    #         )

    #         # 连接信号
    #         signals.process_progress.connect(
    #             self.export_dialog.update_progress)
    #         signals.process_finish.connect(self.on_export_finished)

    #         # 启动导出线程
    #         self.export_worker.start()

    #         self.glogger.info("开始导出视频")

    #     except Exception as e:
    #         self.glogger.error(f"启动导出失败: {e}")
    #         QMessageBox.critical(self, "导出失败", f"启动导出时发生错误:\n{str(e)}")

    # def on_export_finished(self, result):
    #     """导出完成处理"""
    #     if hasattr(self, 'export_dialog'):
    #         self.export_dialog.export_finished(result)

    #     self.glogger.info(f"导出完成: {result}")

    # def cancel_export(self):
    #     """取消导出"""
    #     if hasattr(self, 'export_worker') and self.export_worker.isRunning():
    #         self.glogger.info("正在取消导出...")
    #         self.export_worker.cancel()

    #         # 等待线程结束，最多等待5秒
    #         if not self.export_worker.wait(5000):
    #             # 如果5秒内没有结束，强制终止
    #             self.glogger.warning("强制终止导出线程")
    #             self.export_worker.terminate()
    #             self.export_worker.wait()

    #         self.glogger.info("导出已取消")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.play_pause_all()
        return super().keyPressEvent(event)
