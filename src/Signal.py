# -*- coding: utf-8 -*-

# 三方库
from PyQt5.QtCore import *


class Signal(QObject):
    process_finish = pyqtSignal(str)
    process_progress = pyqtSignal(int)
