# -*- coding: utf-8 -*-

import os
import sys
import tempfile
import subprocess
import configparser
import logging

from PyQt5.QtCore import QObject, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QMessageBox,
    QLineEdit,
    QCheckBox,
    QDialogButtonBox,
)

import requests
import GlobalConfig


class _DownloadWorker(QObject):
    progress = pyqtSignal(int)  # 0-100
    finished = pyqtSignal(str)  # download_path
    error = pyqtSignal(str)
    cancelled = pyqtSignal()    # 用户请求取消并已清理完成

    def __init__(self, url: str, download_path: str, proxies=None, parent=None):
        super().__init__(parent)
        self._url = url
        self._download_path = download_path
        self._proxies = proxies or None
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            download_path = self._download_path
            logger = logging.getLogger(__name__)
            logger.info(f"Update download started: url={self._url}, path={download_path}, proxies={self._proxies!r}")

            with requests.get(self._url, stream=True, timeout=60, proxies=self._proxies) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                downloaded = 0

                with open(download_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if self._is_cancelled:
                            # 取消时删除不完整文件
                            try:
                                f.close()
                            except Exception:
                                pass
                            try:
                                if os.path.exists(download_path):
                                    os.remove(download_path)
                            except Exception:
                                pass
                            logger.info("Update download cancelled by user, temp file removed.")
                            self.cancelled.emit()
                            return

                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total > 0:
                                percent = int(downloaded * 100 / total)
                                self.progress.emit(percent)

            logger.info(f"Update download finished successfully: path={download_path}, size={downloaded} bytes")
            self.finished.emit(download_path)
        except Exception as ex:
            logging.getLogger(__name__).exception("Update download failed: %s", ex)
            self.error.emit(str(ex))


class DownloadUpdateDialog(QDialog):
    """下载更新的进度窗体，独立于主窗体，避免主界面卡死。"""

    def __init__(self, parent, url: str, filename: str):
        super().__init__(parent)
        self._url = url
        self._filename = filename or "installer"

        # 计算下载保存路径
        tmp_dir = tempfile.gettempdir()
        self._download_path = os.path.join(tmp_dir, self._filename)

        # 加载代理配置
        self._proxies = self._load_proxy_config()

        self._thread = QThread(self)
        self._worker = _DownloadWorker(url, self._download_path, self._proxies)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.cancelled.connect(self._on_cancelled)

        # 线程结束时自动回收
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)

        self._init_ui()
        self._thread.start()

    def _init_ui(self):
        self.setWindowTitle("正在下载更新")
        self.setModal(True)
        self.resize(520, 200)

        layout = QVBoxLayout(self)

        self.label = QLabel("正在下载安装包，请稍候……", self)
        layout.addWidget(self.label)

        # 下载链接展示 + 复制按钮
        url_layout = QHBoxLayout()
        url_label = QLabel("下载链接:", self)
        self.url_edit = QLineEdit(self._url, self)
        self.url_edit.setReadOnly(True)
        copy_btn = QPushButton("复制", self)
        copy_btn.clicked.connect(self._copy_url)
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_edit)
        url_layout.addWidget(copy_btn)
        layout.addLayout(url_layout)

        # 保存路径展示 + 打开文件夹按钮
        path_layout = QHBoxLayout()
        path_label = QLabel("保存路径:", self)
        self.path_edit = QLineEdit(self._download_path, self)
        self.path_edit.setReadOnly(True)
        open_btn = QPushButton("打开文件夹", self)
        open_btn.clicked.connect(self._open_folder)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(open_btn)
        layout.addLayout(path_layout)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("0%", self)
        layout.addWidget(self.status_label)

        # 底部按钮：取消 + 代理设置
        btn_layout = QHBoxLayout()
        self.cancel_button = QPushButton("取消", self)
        self.cancel_button.clicked.connect(self._on_cancel)
        self.proxy_button = QPushButton("代理设置...", self)
        self.proxy_button.clicked.connect(self._open_proxy_settings)
        btn_layout.addWidget(self.cancel_button)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.proxy_button)
        layout.addLayout(btn_layout)

    def _on_progress(self, value: int):
        self.progress_bar.setValue(value)
        self.status_label.setText(f"{value}%")

    def _on_finished(self, download_path: str):
        # 下载完成，启动安装程序
        try:
            if sys.platform.startswith("win"):
                subprocess.Popen([download_path], shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", download_path])
            else:
                QMessageBox.information(
                    self,
                    "安装提示",
                    f"已下载安装包：{download_path}\n请手动运行完成安装。",
                )
                self.accept()
                return

            QMessageBox.information(
                self,
                "安装程序已启动",
                "安装程序已启动，请按照向导完成升级。应用将现在退出。",
            )
            # 只关闭下载对话框，不再强制退出主程序
            self.accept()
        except Exception as ex:
            QMessageBox.warning(self, "安装启动失败", f"无法启动安装程序：{ex}")
            self.reject()

    def _on_error(self, message: str):
        QMessageBox.warning(self, "下载失败", f"安装包下载失败：{message}")
        self.reject()

    def _on_cancel(self):
        self._worker.cancel()
        self.cancel_button.setEnabled(False)
        self.status_label.setText("正在取消，请稍候……")

    def _on_cancelled(self):
        """工作线程确认已取消并清理完成后关闭对话框。"""
        self.status_label.setText("已取消")
        logging.getLogger(__name__).info("Update download dialog: cancelled acknowledged by worker.")
        self.reject()

    def closeEvent(self, event):
        # 用户直接关闭对话框时，视为取消
        if self._thread.isRunning():
            self._worker.cancel()
        return super().closeEvent(event)

    # ===== 额外功能：复制链接、打开文件夹、代理设置 =====

    def _copy_url(self):
        from PyQt5.QtWidgets import QApplication as _QApp

        clipboard = _QApp.instance().clipboard()
        clipboard.setText(self._url or "")
        QMessageBox.information(self, "复制成功", "下载链接已复制到剪贴板。")

    def _open_folder(self):
        folder = os.path.dirname(self._download_path)
        if not os.path.isdir(folder):
            QMessageBox.warning(self, "路径不存在", f"文件夹不存在：{folder}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def _open_proxy_settings(self):
        dlg = ProxySettingsDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            # 重新加载代理设置，下次下载生效
            self._proxies = self._load_proxy_config()
            QMessageBox.information(self, "代理设置", "代理设置已保存，下次下载时生效。")

    def _load_proxy_config(self):
        """从全局配置文件中读取代理设置，返回 requests 兼容的 proxies 字典或 None。"""
        config_path = GlobalConfig.CONFIG_FILE_PATH
        if not os.path.exists(config_path):
            return None

        config = configparser.ConfigParser()
        try:
            config.read(config_path, encoding="utf-8")
        except Exception:
            return None

        if not config.has_section("Proxy"):
            return None

        enabled = config.getboolean("Proxy", "enabled", fallback=False)
        proxy_url = config.get("Proxy", "url", fallback="").strip()

        if not enabled or not proxy_url:
            return None

        return {
            "http": proxy_url,
            "https": proxy_url,
        }


class ProxySettingsDialog(QDialog):
    """更新下载使用的简单代理设置对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("代理设置")
        self.resize(420, 160)

        layout = QVBoxLayout(self)

        self.enable_checkbox = QCheckBox("启用代理下载", self)
        layout.addWidget(self.enable_checkbox)

        row = QHBoxLayout()
        row.addWidget(QLabel("代理地址:", self))
        self.proxy_edit = QLineEdit(self)
        self.proxy_edit.setPlaceholderText("例如：http://127.0.0.1:7890")
        row.addWidget(self.proxy_edit)
        layout.addLayout(row)

        hint = QLabel(
            "说明：仅用于更新下载请求，建议填写完整协议+主机+端口，例如 http://127.0.0.1:7890", self)
        hint.setWordWrap(True)
        layout.addWidget(hint)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self._load()

    def _load(self):
        config_path = GlobalConfig.CONFIG_FILE_PATH
        config = configparser.ConfigParser()
        if os.path.exists(config_path):
            try:
                config.read(config_path, encoding="utf-8")
            except Exception:
                return

        if config.has_section("Proxy"):
            enabled = config.getboolean("Proxy", "enabled", fallback=False)
            url = config.get("Proxy", "url", fallback="")
            self.enable_checkbox.setChecked(enabled)
            self.proxy_edit.setText(url)

    def _on_accept(self):
        enabled = self.enable_checkbox.isChecked()
        url = self.proxy_edit.text().strip()

        if enabled and not url:
            QMessageBox.warning(self, "设置错误", "已勾选启用代理，但代理地址为空。")
            return

        config_path = GlobalConfig.CONFIG_FILE_PATH
        config = configparser.ConfigParser()
        if os.path.exists(config_path):
            try:
                config.read(config_path, encoding="utf-8")
            except Exception:
                # 如果读取失败，则从空配置开始
                config = configparser.ConfigParser()

        if not config.has_section("Proxy"):
            config.add_section("Proxy")

        config.set("Proxy", "enabled", "true" if enabled else "false")
        config.set("Proxy", "url", url)

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                config.write(f)
        except Exception as ex:
            QMessageBox.warning(self, "保存失败", f"写入配置文件失败：{ex}")
            return

        self.accept()
