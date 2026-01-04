# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sys
import logging
import subprocess
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List

import requests

from utils import send_win_notification

logger = logging.getLogger(__name__)


class Notifier:
    def __init__(
        self,
        enable_system: bool = True,
        enable_email: bool = False,
        enable_wechat: bool = False,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_pass: Optional[str] = None,
        smtp_from: Optional[str] = None,
        smtp_to: Optional[List[str]] = None,
        use_ssl: Optional[bool] = None,
        use_tls: Optional[bool] = None,
        wechat_webhook: Optional[str] = None,
        wechat_mentions: Optional[List[str]] = None,
    ) -> None:
        self.enable_system = enable_system
        self.enable_email = enable_email
        self.enable_wechat = enable_wechat or (os.getenv("WECHAT_ENABLE") == "1")

        self.wechat_webhook = wechat_webhook or os.getenv("WECHAT_WEBHOOK")
        if wechat_mentions is not None:
            self.wechat_mentions = wechat_mentions
        else:
            mentions_env = os.getenv("WECHAT_MENTIONS")
            self.wechat_mentions = [x.strip() for x in mentions_env.split(",") if x.strip()] if mentions_env else []

        self.smtp_host = smtp_host or os.getenv("SMTP_HOST")
        self.smtp_port = int(smtp_port or os.getenv("SMTP_PORT") or 587)
        self.smtp_user = smtp_user or os.getenv("SMTP_USER")
        self.smtp_pass = smtp_pass or os.getenv("SMTP_PASS")
        self.smtp_from = smtp_from or os.getenv("SMTP_FROM") or self.smtp_user
        to_env = os.getenv("SMTP_TO")
        self.smtp_to = smtp_to or ([x.strip() for x in to_env.split(",") if x.strip()] if to_env else [])

        env_ssl = os.getenv("SMTP_SSL")
        env_tls = os.getenv("SMTP_TLS", "1")
        self.use_ssl = use_ssl if use_ssl is not None else (env_ssl == "1")
        self.use_tls = use_tls if use_tls is not None else (env_tls == "1")

    def notify(self, title: str, message: str) -> None:
        def _do_notify() -> None:
            if self.enable_system:
                try:
                    self._system_notify(title, message)
                except Exception:
                    logger.exception("Failed to notify system")
            if self.enable_email:
                try:
                    self._email_notify(title, message)
                except Exception:
                    logger.exception("Failed to notify email")
            if self.enable_wechat:
                try:
                    self._wechat_notify(title, message)
                except Exception:
                    logger.exception("Failed to notify wechat")

        try:
            import threading

            threading.Thread(target=_do_notify, daemon=True).start()
        except Exception:
            _do_notify()

    def _system_notify(self, title: str, message: str) -> None:
        msg = message if len(message) <= 220 else (message[:217] + "...")
        if sys.platform == "darwin":
            subprocess.run([
                "osascript",
                "-e",
                f'display notification "{msg}" with title "{title}"',
            ], check=False)
        elif sys.platform.startswith("win"):
            try:
                send_win_notification(title, msg)
            except Exception:
                logger.exception("Failed to notify system")

    def _email_notify(self, title: str, message: str) -> None:
        if not (self.smtp_host and self.smtp_from and self.smtp_to and self.smtp_user and self.smtp_pass):
            return

        mime = MIMEMultipart()
        mime["From"] = self.smtp_from
        mime["To"] = ", ".join(self.smtp_to)
        mime["Subject"] = title
        mime.attach(MIMEText(message, "plain", "utf-8"))

        if self.use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as server:
                server.login(self.smtp_user, self.smtp_pass)
                server.sendmail(self.smtp_from, self.smtp_to, mime.as_string())
        else:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                if self.use_tls:
                    server.starttls(context=ssl.create_default_context())
                server.login(self.smtp_user, self.smtp_pass)
                server.sendmail(self.smtp_from, self.smtp_to, mime.as_string())

    def _wechat_notify(self, title: str, message: str) -> None:
        if not self.wechat_webhook:
            return

        content = f"{title}\n{message}"
        payload = {
            "msgtype": "text",
            "text": {
                "content": content,
                "mentioned_mobile_list": self.wechat_mentions or [],
            },
        }

        try:
            requests.post(self.wechat_webhook, json=payload, timeout=8)
        except Exception:
            logger.exception("Failed to notify wechat")
