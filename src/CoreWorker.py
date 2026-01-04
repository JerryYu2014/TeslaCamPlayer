# -*- coding: utf-8 -*-

# 标准库
import time
import logging

# 三方库
from PyQt5.QtCore import *

# 自研库
from Signal import Signal
# import GlobalConfig
# from utils import logger


class CoreWorker(QThread):
    def __init__(self, parent, signals: Signal, inputFolder, outputFolder):
        super().__init__(parent)

        self.parent = parent
        self.signals = signals

        self.inputFolder = inputFolder
        self.outputFolder = outputFolder

        # self.glogger = logger(GlobalConfig.LOG_DIR, False,
        #                       f"TeslaCamPlayer-CoreWorker-{id(self)}")
        self.glogger = logging.getLogger("TeslaCamPlayer-CoreWorker")

    def work(self):
        self.glogger.info("处理中...")
        time.sleep(1)

    def run(self):
        try:
            self.work()
            self.glogger.info("处理完成")
            self.signals.process_finish.emit('success')
        except Exception as e:
            self.glogger.error(f"处理失败: {str(e)}")
            self.signals.process_finish.emit("fail")
