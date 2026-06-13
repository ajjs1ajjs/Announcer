import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set

from announcer.config import Config
from announcer.football import FootballAPI
from announcer.thesportsdb import TheSportsDBAPI
from announcer.formatter import _team_flag
from announcer.telegram_bot import TelegramBot


STATE_FILE = os.path.join(os.path.dirname(__file__), "pre_match_state.json")
NOTIFY_MINUTES_BEFORE = 15
NOTIFY_WINDOW_MINUTES = 20


def _load_state() -> Dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_state(state: Dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)


def _match_key(match: Dict) -> str:
    home = match.get("home_team", "")
    away = match.get("away_team", "")
    date = match.get("date", "")
    comp = match.get("competition", "")
    return f"{comp}|{home}|{away}|{date}"


def _parse_match_dt(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%d.%m.%Y %H:%M")
    except ValueError:
        return None


def _format_pre_match(match: Dict) -> str:
    comp = match.get("competition", "")
    emblem = match.get("emblem", "⚽")
    date = match.get("date", "???")
    home = match.get("home_team") or "?"
    away = match.get("away_team") or "?"
    home_flag = _team_flag(home)
    away_flag = _team_flag(away)
    venue = match.get("venue", "")
    stage = match.get("stage", "")
    group = match.get("group", "")

    stage_info = ""
    if stage and stage != "REGULAR_SEASON":
        stage_info = stage.replace("_", " ").title()
    if group:
        stage_info = f"{stage_info} | Group {group}" if stage_info else f"Group {group}"

    lines = [
        f"<b>⚽️ МАТЧ ПОЧИНАЄТЬСЯ ЧЕРЕЗ {NOTIFY_MINUTES_BEFORE} ХВИЛИН!</b>\n",
        f"{emblem} <b>{comp}</b>",
        f"  📅 {date}",
        f"  {home_flag} {home} vs {away_flag} {away}",
    ]

    if stage_info:
        lines.append(f"  {stage_info.strip()}")

    if venue:
        lines.append(f"  📍 {venue}")

    lines.append("  ─────────────────")
    return "\n".join(lines)


def main():
    try:
        config = Config.from_env()
    except KeyError as e:
        print(f"Missing environment variable: {e}")
        sys.exit(1)

    bot = TelegramBot(config)
    state = _load_state()
    notified: Set[str] = set(state.get("notified", []))

    now = datetime.now()
    today_str = now.strftime("%d.%m.%Y")

    notified = {k for k in notified if today_str in k}

    football_api = FootballAPI(config)
    football_matches: List[Dict] = []

    try:
        football_matches = football_api.get_upcoming_matches()
        print(f"Football matches found: {len(football_matches)}")
    except Exception as e:
        print(f"Football API error: {e}")

    try:
        extra = TheSportsDBAPI(config).get_upcoming_matches()
        print(f"TheSportsDB matches found: {len(extra)}")
        football_matches.extend(extra)
    except Exception as e:
        print(f"TheSportsDB API error: {e}")

    football_matches.sort(key=lambda m: m.get("date") or "")

    sent = 0
    for match in football_matches:
        match_dt = _parse_match_dt(match.get("date", ""))
        if not match_dt:
            continue

        minutes_until = (match_dt - now).total_seconds() / 60

        if 0 < minutes_until <= NOTIFY_WINDOW_MINUTES:
            key = _match_key(match)
            if key not in notified:
                msg = _format_pre_match(match)
                ok = bot.send_message(msg)
                if ok:
                    notified.add(key)
                    sent += 1
                    print(f"Sent pre-match: {match.get('home_team')} vs {match.get('away_team')}")
                else:
                    print(f"Failed to send: {match.get('home_team')} vs {match.get('away_team')}")

    state["notified"] = list(notified)
    state["last_run"] = now.isoformat()
    _save_state(state)

    print(f"Pre-match notifications sent: {sent}")


if __name__ == "__main__":
    main()
