import sys, requests
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

# Test simple message first
token = "8889473896:AAFPOmXuqq0py0p4Ne4LGuIVxylBqLMYieA"
chat_id = "-1003903136690"

r = requests.post(
    f"https://api.telegram.org/bot{token}/sendMessage",
    json={"chat_id": chat_id, "text": "test 123", "parse_mode": "HTML"},
    timeout=30,
)
print(f"Simple test: {r.status_code} {r.text[:500]}")

# Now full digest
from announcer.config import Config
from announcer.football import FootballAPI
from announcer.boxing import BoxingAPI
from announcer.formatter import format_daily_digest
from announcer.telegram_bot import TelegramBot

cfg = Config(token, token, chat_id, timezone_offset=3, days_ahead=7)
cfg.telegram_bot_token = token
matches = FootballAPI(cfg).get_upcoming_matches()
boxing = BoxingAPI().get_upcoming_events()
print(f"Football: {len(matches)}, Boxing: {len(boxing)}")
digest = format_daily_digest(matches, boxing)
print(f"Digest length: {len(digest)} chars")
bot = TelegramBot(cfg)
bot.token = token
bot.api_url = f"https://api.telegram.org/bot{token}"
result = bot.send_long_message(digest)
print(f"send_long_message: {result}")
