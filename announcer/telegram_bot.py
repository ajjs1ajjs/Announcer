from typing import List

import requests

from .config import Config


class TelegramBot:
    BASE_URL = "https://api.telegram.org/bot"

    def __init__(self, config: Config):
        self.token = config.telegram_bot_token
        self.chat_id = config.telegram_chat_id
        self.api_url = f"{self.BASE_URL}{self.token}"

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        try:
            resp = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True,
                },
                timeout=15,
            )
            resp.raise_for_status()
            return True
        except requests.RequestException:
            return False

    def send_long_message(self, text: str, max_len: int = 4000) -> bool:
        parts = self._split(text, max_len)
        success = True
        for part in parts:
            ok = self.send_message(part)
            if not ok:
                success = False
        return success

    @staticmethod
    def _split(text: str, max_len: int) -> List[str]:
        if len(text) <= max_len:
            return [text]

        parts = []
        current = ""
        for line in text.split("\n"):
            candidate = (current + "\n" + line).strip()
            if len(candidate) > max_len:
                if current:
                    parts.append(current)
                current = line
            else:
                current = candidate

        if current:
            parts.append(current)

        return parts

    def send_error(self, error_msg: str) -> bool:
        text = f"<b>⚠️ Помилка</b>\n<pre>{error_msg}</pre>"
        return self.send_message(text)
