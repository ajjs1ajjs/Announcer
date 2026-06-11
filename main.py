import sys
import traceback

from announcer.config import Config
from announcer.football import FootballAPI
from announcer.boxing import BoxingAPI
from announcer.thesportsdb import TheSportsDBAPI
from announcer.formatter import format_daily_digest
from announcer.telegram_bot import TelegramBot


def main():
    try:
        config = Config.from_env()
    except KeyError as e:
        print(f"Missing environment variable: {e}")
        sys.exit(1)

    bot = TelegramBot(config)

    football_api = FootballAPI(config)
    boxing_api = BoxingAPI(days_ahead=config.days_ahead)

    try:
        football_matches = football_api.get_upcoming_matches()
        print(f"Football matches found: {len(football_matches)}")
    except Exception as e:
        print(f"Football API error: {e}")
        bot.send_error(f"Football API: {e}")
        football_matches = []

    try:
        extra_matches = TheSportsDBAPI(config).get_upcoming_matches()
        print(f"TheSportsDB matches found: {len(extra_matches)}")
        football_matches.extend(extra_matches)
        football_matches.sort(key=lambda m: m.get("date") or "")
    except Exception as e:
        print(f"TheSportsDB API error: {e}")

    try:
        boxing_events = boxing_api.get_upcoming_events()
        print(f"Boxing events found: {len(boxing_events)}")
    except Exception as e:
        print(f"Boxing API error: {e}")
        bot.send_error(f"Boxing API: {e}")
        boxing_events = []

    if not football_matches and not boxing_events:
        print("No events today, skipping")
        return

    digest = format_daily_digest(football_matches, boxing_events)
    success = bot.send_long_message(digest)

    if success:
        print("Digest sent successfully")
    else:
        print("Failed to send digest")
        sys.exit(1)


if __name__ == "__main__":
    main()
