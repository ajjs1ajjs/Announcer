from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from urllib.parse import urlencode

import requests

from .config import Config


COMPETITION_EMOJIS: Dict[str, str] = {
    "FIFA World Cup": "🏆",
    "European Championship": "🇪🇺",
    "UEFA Nations League": "🏟️",
    "UEFA Champions League": "⭐",
    "UEFA Europa League": "🌍",
    "UEFA Conference League": "🌐",
    "FIFA Club World Cup": "🌎",
}

AREA_FLAGS: Dict[str, str] = {
    "ARG": "🇦🇷", "BRA": "🇧🇷", "ENG": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "ESP": "🇪🇸", "FRA": "🇫🇷", "GER": "🇩🇪", "ITA": "🇮🇹",
    "NED": "🇳🇱", "POR": "🇵🇹", "URU": "🇺🇾", "BEL": "🇧🇪",
    "CRO": "🇭🇷", "SUI": "🇨🇭", "COL": "🇨🇴", "MEX": "🇲🇽",
    "UKR": "🇺🇦", "POL": "🇵🇱", "HUN": "🇭🇺", "AUT": "🇦🇹",
    "SCO": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "WAL": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
}


class FootballAPI:
    BASE_URL = "https://api.football-data.org/v4"

    def __init__(self, config: Config):
        self.api_key = config.football_api_key
        self.headers = {"X-Auth-Token": self.api_key}
        self.target_names = config.football_competitions
        self.days_ahead = config.days_ahead
        self.tz_offset = config.timezone_offset

    def _request(self, path: str, params: Optional[Dict] = None) -> Dict:
        url = f"{self.BASE_URL}{path}"
        if params:
            url += f"?{urlencode(params)}"
        resp = requests.get(url, headers=self.headers, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def _get_all_competitions(self) -> List[Dict]:
        data = self._request("/competitions")
        return data.get("competitions", [])

    def _match_competitions(self, all_comps: List[Dict]) -> List[Dict]:
        matched = []
        target_set = {n.strip() for n in self.target_names}
        for comp in all_comps:
            name = comp.get("name", "")
            code = comp.get("code", "")
            if name in target_set or code in target_set:
                matched.append(comp)
        return matched

    def get_upcoming_matches(self) -> List[Dict]:
        all_comps = self._get_all_competitions()
        matched = self._match_competitions(all_comps)

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        until = (datetime.now(timezone.utc) + timedelta(days=self.days_ahead)).strftime("%Y-%m-%d")

        results: List[Dict] = []
        for comp in matched:
            comp_id = comp["id"]
            comp_name = comp["name"]
            try:
                data = self._request(
                    f"/competitions/{comp_id}/matches",
                    {"dateFrom": today, "dateTo": until, "status": "SCHEDULED,TIMED"},
                )
            except requests.RequestException:
                continue

            for match in data.get("matches", []):
                utc_str = match.get("utcDate", "")
                parsed = self._parse_date(utc_str)
                results.append({
                    "competition": comp_name,
                    "emblem": COMPETITION_EMOJIS.get(comp_name, "⚽"),
                    "home_team": match.get("homeTeam", {}).get("name", "?"),
                    "away_team": match.get("awayTeam", {}).get("name", "?"),
                    "home_crest": match.get("homeTeam", {}).get("crest", ""),
                    "away_crest": match.get("awayTeam", {}).get("crest", ""),
                    "date": parsed,
                    "venue": match.get("venue", ""),
                    "stage": match.get("stage", ""),
                    "group": match.get("group", ""),
                    "score_home": match.get("score", {}).get("fullTime", {}).get("home"),
                    "score_away": match.get("score", {}).get("fullTime", {}).get("away"),
                })

        results.sort(key=lambda m: m["date"] or "")
        return results

    def _parse_date(self, utc_str: str) -> Optional[str]:
        if not utc_str:
            return None
        try:
            dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
            local = dt + timedelta(hours=self.tz_offset)
            return local.strftime("%d.%m.%Y %H:%M")
        except (ValueError, TypeError):
            return None
