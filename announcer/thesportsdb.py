from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import requests

from .config import Config


COMPETITION_EMOJIS: Dict[str, str] = {
    "UEFA Nations League": "🏟️",
    "UEFA Europa League": "🌍",
    "UEFA Conference League": "🌐",
    "FIFA Club World Cup": "🌎",
    "UEFA Champions League": "⭐",
    "FIFA World Cup": "🏆",
    "European Championship": "🇪🇺",
}

# TheSportsDB free API key "3" gives read-only access
BASE_URL = "https://www.thesportsdb.com/api/v1/json/3"

# League IDs for our target competitions
LEAGUES = {
    "UEFA Nations League": 4490,
    "UEFA Champions League": 4480,
    "UEFA Europa League": 4481,
    "UEFA Conference League": 5071,
    "FIFA Club World Cup": 4503,
}

# Teams that are NOT part of these comps (filter out domestic leagues)
DOMESTIC_LEAGUE_TEAMS: set = set()


class TheSportsDBAPI:
    def __init__(self, config: Config):
        self.days_ahead = config.days_ahead
        self.tz_offset = config.timezone_offset

    def get_upcoming_matches(self) -> List[Dict]:
        results: List[Dict] = []
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        for comp_name, league_id in LEAGUES.items():
            try:
                data = self._request(f"/eventsnextleague.php?id={league_id}")
                if not data:
                    continue
                events = data.get("events", [])
                if not events:
                    continue

                for ev in events:
                    match = self._parse_event(ev, comp_name)
                    if match:
                        match_date = match.get("_date_obj")
                        if match_date:
                            match_day = match_date.replace(hour=0, minute=0, second=0, microsecond=0)
                            if match_day < today - timedelta(days=1) or match_day > today + timedelta(days=self.days_ahead):
                                continue
                        results.append(match)
            except requests.RequestException:
                continue

        results.sort(key=lambda m: m.get("date") or "")
        return results

    def _request(self, path: str) -> Optional[Dict]:
        url = f"{BASE_URL}{path}"
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            return None
        try:
            return resp.json()
        except (ValueError, requests.exceptions.JSONDecodeError):
            return None

    @staticmethod
    def _competition_emoji(name: str) -> str:
        for key, emoji in COMPETITION_EMOJIS.items():
            if key.lower() in name.lower():
                return emoji
        return "⚽"

    def _parse_event(self, ev: Dict, comp_name: str) -> Optional[Dict]:
        home = ev.get("strHomeTeam") or ""
        away = ev.get("strAwayTeam") or ""
        venue = ev.get("strVenue", "") or ""
        thumb = ev.get("strThumb", "") or ""

        if not home or not away:
            return None

        date_obj = self._parse_timestamp(ev.get("strTimestamp", ""))
        display_date = self._format_date(date_obj) if date_obj else ev.get("dateEvent", "?")

        return {
            "competition": comp_name,
            "emblem": self._competition_emoji(comp_name),
            "home_team": home,
            "away_team": away,
            "home_crest": thumb,
            "away_crest": "",
            "date": display_date,
            "venue": venue,
            "stage": "",
            "group": "",
            "source": "thesportsdb",
            "_date_obj": date_obj,
        }

    def _parse_timestamp(self, ts: str) -> Optional[datetime]:
        if not ts:
            return None
        try:
            if "T" in ts:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                local = dt + timedelta(hours=self.tz_offset)
                return local
            parts = ts.split("-")
            if len(parts) == 3:
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                return datetime(year, month, day)
        except (ValueError, IndexError):
            pass
        return None

    def _format_date(self, dt: datetime) -> str:
        return dt.strftime("%d.%m.%Y %H:%M")
