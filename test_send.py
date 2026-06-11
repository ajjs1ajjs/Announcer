import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from announcer.football import FootballAPI
from announcer.config import Config
from announcer.formatter import format_digest
from announcer.telegram_bot import send_long_message

cfg = Config(
    "bbb39e45edba41b9be3c7f89bfde58c2",
    "7336475367:AAGPDDUC4IdopHjOhBc9-T83b52Gj1OjBvg",
    "-1003903136690",
    timezone_offset=3,
    days_ahead=7,
)

matches = FootballAPI(cfg).get_upcoming_matches()
body = format_digest(matches, [])
print(f"Message length: {len(body)} chars")
print(body[:500])
print("---")
r = send_long_message(cfg.telegram_bot_token, cfg.telegram_chat_id, body)
print(f"Telegram result: {r}")
