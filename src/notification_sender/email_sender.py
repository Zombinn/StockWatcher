"""SMTP 邮件通知"""
from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

from .base import BaseSender

logger = logging.getLogger(__name__)


class EmailSender(BaseSender):
    """基于 SMTP 的邮件发送器"""

    def __init__(self, server: str, port: int, user: str, password: str, to: str):
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        # EMAIL_TO 支持逗号分隔多个收件人
        self.recipients = [a.strip() for a in to.split(",") if a.strip()]

    def _send(self, subject: str, body: str, subtype: str) -> bool:
        if not self.recipients:
            logger.error("邮件发送失败: 未配置 EMAIL_TO")
            return False
        try:
            msg = MIMEText(body, subtype, "utf-8")
            msg["Subject"] = subject or "StockWatcher 通知"
            msg["From"] = formataddr(("StockWatcher", self.user))
            msg["To"] = ", ".join(self.recipients)

            if self.port == 465:
                client = smtplib.SMTP_SSL(self.server, self.port, timeout=20)
            else:
                client = smtplib.SMTP(self.server, self.port, timeout=20)
                client.starttls()
            with client:
                client.login(self.user, self.password)
                client.sendmail(self.user, self.recipients, msg.as_string())
            return True
        except Exception as e:
            logger.error("邮件发送失败: %s", e)
            return False

    async def send_text(self, message: str, title: str = "") -> bool:
        return self._send(title, message, "plain")

    async def send_markdown(self, content: str, title: str = "") -> bool:
        # 邮件不渲染 Markdown，用 <pre> 保留排版
        html = f"<pre style='font-family:monospace;white-space:pre-wrap'>{content}</pre>"
        return self._send(title, html, "html")
