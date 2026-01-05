# -*- coding: utf-8 -*-

import os
import sys
import tempfile
import subprocess

from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QMessageBox

import requests


class _DownloadWorker(QObject):
    progress = pyqtSignal(int)  # 0-100
    finished = pyqtSignal(str)  # download_path
    error = pyqtSignal(str)

    def __init__(self, url: str, filename: str, parent=None):
        super().__init__(parent)
        self._url = url
        self._filename = filename or "installer"
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            tmp_dir = tempfile.gettempdir()
            download_path = os.path.join(tmp_dir, self._filename)

            with requests.get(self._url, stream=True, timeout=60) as r:
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
                            return

                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total > 0:
                                percent = int(downloaded * 100 / total)
                                self.progress.emit(percent)

            self.finished.emit(download_path)
        except Exception as ex:
            self.error.emit(str(ex))


class DownloadUpdateDialog(QDialog):
    """下载更新的进度窗体，独立于主窗体，避免主界面卡死。"""

    def __init__(self, parent, url: str, filename: str):
        super().__init__(parent)
        self._url = url
        self._filename = filename

        self._thread = QThread(self)
        self._worker = _DownloadWorker(url, filename)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)

        # 线程结束时自动回收
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)

        self._init_ui()
        self._thread.start()

    def _init_ui(self):
        self.setWindowTitle("正在下载更新")
        self.setModal(True)
        self.resize(400, 120)

        layout = QVBoxLayout(self)

        self.label = QLabel("正在下载安装包，请稍候……", self)
        layout.addWidget(self.label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("0%", self)
        layout.addWidget(self.status_label)

        self.cancel_button = QPushButton("取消", self)
        self.cancel_button.clicked.connect(self._on_cancel)
        layout.addWidget(self.cancel_button)

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
                    parent=self,
                )
                self.accept()
                return

            QMessageBox.information(
                self,
                "安装程序已启动",
                "安装程序已启动，请按照向导完成升级。应用将现在退出。",
                parent=self,
            )
            # 关闭对话框并退出应用
            self.accept()
            from PyQt5.QtWidgets import QApplication as _QApp

            _QApp.instance().quit()
        except Exception as ex:
            QMessageBox.warning(self, "安装启动失败", f"无法启动安装程序：{ex}", parent=self)
            self.reject()

    def _on_error(self, message: str):
        QMessageBox.warning(self, "下载失败", f"安装包下载失败：{message}", parent=self)
        self.reject()

    def _on_cancel(self):
        self._worker.cancel()
        self.cancel_button.setEnabled(False)
        self.status_label.setText("正在取消，请稍候……")

    def closeEvent(self, event):
        # 用户直接关闭对话框时，视为取消
        if self._thread.isRunning():
            self._worker.cancel()
        return super().closeEvent(event)
