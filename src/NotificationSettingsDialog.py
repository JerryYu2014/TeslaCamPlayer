# -*- coding: utf-8 -*-
from __future__ import annotations

import configparser
import os
from typing import Any, Dict

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

import GlobalConfig


class NotificationSettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("通知设置")
        self.resize(480, 360)

        root = QVBoxLayout(self)

        self.chkSystem = QCheckBox("系统通知", self)
        root.addWidget(self.chkSystem)

        self.emailForm = QFormLayout()
        self.emailForm.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        self.edHost = QLineEdit(self)
        self.edHost.setPlaceholderText("SMTP服务器，如 smtp.qq.com")
        self.spinPort = QLineEdit(self)
        self.spinPort.setPlaceholderText("端口，如 465 或 587")
        self.edUser = QLineEdit(self)
        self.edPass = QLineEdit(self)
        self.edPass.setEchoMode(QLineEdit.Password)
        self.edFrom = QLineEdit(self)
        self.edTo = QLineEdit(self)
        self.edTo.setPlaceholderText("多个收件人用逗号分隔")
        self.chkSSL = QCheckBox("使用SSL", self)
        self.chkTLS = QCheckBox("使用TLS", self)

        for w in (self.edHost, self.spinPort, self.edUser, self.edPass, self.edFrom, self.edTo):
            sp = w.sizePolicy()
            sp.setHorizontalStretch(1)
            w.setSizePolicy(sp)

        self.emailForm.addRow("SMTP 主机", self.edHost)
        self.emailForm.addRow("SMTP 端口", self.spinPort)
        self.emailForm.addRow("SMTP 用户", self.edUser)
        self.emailForm.addRow("SMTP 密码/授权码", self.edPass)
        self.emailForm.addRow("发件人 From", self.edFrom)
        self.emailForm.addRow("收件人 To", self.edTo)
        self.emailForm.addRow(self.chkSSL, self.chkTLS)

        self.emailGroup = QGroupBox("邮件通知", self)
        self.emailGroup.setCheckable(True)
        self.emailGroup.setLayout(self.emailForm)
        root.addWidget(self.emailGroup)

        self.wechatForm = QFormLayout()
        self.wechatForm.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.edWebhook = QLineEdit(self)
        self.edWebhook.setPlaceholderText("企业微信机器人 Webhook URL")
        self.edMentions = QLineEdit(self)
        self.edMentions.setPlaceholderText("需要@的手机号，逗号分隔，可留空")

        for w in (self.edWebhook, self.edMentions):
            sp = w.sizePolicy()
            sp.setHorizontalStretch(1)
            w.setSizePolicy(sp)

        self.wechatForm.addRow("Webhook", self.edWebhook)
        self.wechatForm.addRow("@手机号", self.edMentions)

        self.wechatGroup = QGroupBox("微信通知", self)
        self.wechatGroup.setCheckable(True)
        self.wechatGroup.setLayout(self.wechatForm)
        root.addWidget(self.wechatGroup)

        root.addStretch(1)

        btns = QHBoxLayout()
        self.btnOk = QPushButton("确定", self)
        self.btnCancel = QPushButton("取消", self)
        btns.addStretch(1)
        btns.addWidget(self.btnOk)
        btns.addWidget(self.btnCancel)
        root.addLayout(btns)

        self.btnOk.clicked.connect(self.accept)
        self.btnCancel.clicked.connect(self.reject)

        self._load_from_config()

    def notify_values(self) -> Dict[str, Any]:
        return {
            "notify_system": self.chkSystem.isChecked(),
            "notify_email": bool(self.emailGroup.isChecked()),
        }

    def wechat_values(self) -> Dict[str, Any]:
        return {
            "enable_wechat": bool(self.wechatGroup.isChecked()),
            "webhook": self.edWebhook.text().strip() or None,
            "mentions": self.edMentions.text().strip() or None,
        }

    def email_values(self) -> Dict[str, Any]:
        port_text = self.spinPort.text().strip()
        try:
            port_value = int(port_text) if port_text else None
        except ValueError:
            port_value = None

        return {
            "smtp_host": self.edHost.text().strip() or None,
            "smtp_port": port_value,
            "smtp_user": self.edUser.text().strip() or None,
            "smtp_pass": self.edPass.text(),
            "smtp_from": self.edFrom.text().strip() or None,
            "smtp_to": self.edTo.text().strip() or None,
            "use_ssl": self.chkSSL.isChecked(),
            "use_tls": self.chkTLS.isChecked(),
        }

    def accept(self) -> None:
        self._save_to_config()
        super().accept()

    def _load_from_config(self) -> None:
        config_path = GlobalConfig.CONFIG_FILE_PATH
        if not os.path.exists(config_path):
            return

        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')

        section = "Notification"
        if not config.has_section(section):
            return

        get = config.get
        getboolean = config.getboolean

        try:
            self.chkSystem.setChecked(getboolean(section, "notify_system", fallback=True))
        except Exception:
            self.chkSystem.setChecked(True)

        try:
            self.emailGroup.setChecked(getboolean(section, "notify_email", fallback=False))
        except Exception:
            self.emailGroup.setChecked(False)

        try:
            self.wechatGroup.setChecked(getboolean(section, "notify_wechat", fallback=False))
        except Exception:
            self.wechatGroup.setChecked(False)

        self.edHost.setText(get(section, "smtp_host", fallback=""))
        port = get(section, "smtp_port", fallback="")
        self.spinPort.setText(port)
        self.edUser.setText(get(section, "smtp_user", fallback=""))
        self.edPass.setText(get(section, "smtp_pass", fallback=""))
        self.edFrom.setText(get(section, "smtp_from", fallback=""))
        self.edTo.setText(get(section, "smtp_to", fallback=""))

        self.chkSSL.setChecked(config.getboolean(section, "use_ssl", fallback=False))
        self.chkTLS.setChecked(config.getboolean(section, "use_tls", fallback=True))

        self.edWebhook.setText(get(section, "wechat_webhook", fallback=""))
        self.edMentions.setText(get(section, "wechat_mentions", fallback=""))

    def _save_to_config(self) -> None:
        config_path = GlobalConfig.CONFIG_FILE_PATH

        config = configparser.ConfigParser()
        if os.path.exists(config_path):
            config.read(config_path, encoding='utf-8')

        section = "Notification"
        if not config.has_section(section):
            config.add_section(section)

        notify_vals = self.notify_values()
        email_vals = self.email_values()
        wechat_vals = self.wechat_values()

        config.set(section, "notify_system", "1" if notify_vals["notify_system"] else "0")
        config.set(section, "notify_email", "1" if notify_vals["notify_email"] else "0")
        config.set(section, "notify_wechat", "1" if wechat_vals["enable_wechat"] else "0")

        config.set(section, "smtp_host", email_vals["smtp_host"] or "")
        config.set(section, "smtp_port", "" if email_vals["smtp_port"] is None else str(email_vals["smtp_port"]))
        config.set(section, "smtp_user", email_vals["smtp_user"] or "")
        config.set(section, "smtp_pass", email_vals["smtp_pass"] or "")
        config.set(section, "smtp_from", email_vals["smtp_from"] or "")
        config.set(section, "smtp_to", email_vals["smtp_to"] or "")
        config.set(section, "use_ssl", "1" if email_vals["use_ssl"] else "0")
        config.set(section, "use_tls", "1" if email_vals["use_tls"] else "0")

        config.set(section, "wechat_webhook", wechat_vals["webhook"] or "")
        config.set(section, "wechat_mentions", wechat_vals["mentions"] or "")

        with open(config_path, "w", encoding="utf-8") as f:
            config.write(f)
