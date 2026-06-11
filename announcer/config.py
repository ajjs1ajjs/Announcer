import os
from dataclasses import dataclass, field
from typing import List


DEFAULT_COMPETITIONS = [
    "FIFA World Cup",
    "European Championship",
    "UEFA Nations League",
    "UEFA Champions League",
    "UEFA Europa League",
    "UEFA Conference League",
    "FIFA Club World Cup",
]


@dataclass
class Config:
    football_api_key: str
    telegram_bot_token: str
    telegram_chat_id: str
    football_competitions: List[str] = field(default_factory=lambda: DEFAULT_COMPETITIONS)
    days_ahead: int = 0
    timezone_offset: int = 3

    @classmethod
    def from_env(cls) -> "Config":
        comps_raw = os.environ.get("FOOTBALL_COMPETITIONS")
        competitions = (
            [c.strip() for c in comps_raw.split(",") if c.strip()]
            if comps_raw
            else DEFAULT_COMPETITIONS
        )
        return cls(
            football_api_key=os.environ["FOOTBALL_API_KEY"],
            telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
            telegram_chat_id=os.environ["TELEGRAM_CHAT_ID"],
            football_competitions=competitions,
            days_ahead=int(os.environ.get("DAYS_AHEAD", "7")),
            timezone_offset=int(os.environ.get("TIMEZONE_OFFSET", "3")),
        )
