import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup


MONTH_NAMES = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}

COMPETITION_EMOJIS: Dict[str, str] = {
    "UEFA Nations League": "🏟️",
    "UEFA Europa League": "🌍",
    "UEFA Conference League": "🌐",
    "FIFA Club World Cup": "🌎",
}

TEAM_FLAGS: Dict[str, str] = {
    "Brazil": "🇧🇷", "Argentina": "🇦🇷", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Spain": "🇪🇸", "France": "🇫🇷", "Germany": "🇩🇪", "Italy": "🇮🇹",
    "Netherlands": "🇳🇱", "Portugal": "🇵🇹", "Uruguay": "🇺🇾",
    "Belgium": "🇧🇪", "Croatia": "🇭🇷", "Switzerland": "🇨🇭",
    "Colombia": "🇨🇴", "Mexico": "🇲🇽", "Ukraine": "🇺🇦",
    "Poland": "🇵🇱", "Hungary": "🇭🇺", "Austria": "🇦🇹",
    "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    "USA": "🇺🇸", "Canada": "🇨🇦", "Japan": "🇯🇵", "South Korea": "🇰🇷",
    "Australia": "🇦🇺", "Nigeria": "🇳🇬", "Senegal": "🇸🇳",
    "Morocco": "🇲🇦", "Egypt": "🇪🇬", "Ghana": "🇬🇭",
    "Algeria": "🇩🇿", "Tunisia": "🇹🇳", "Ivory Coast": "🇨🇮",
    "Denmark": "🇩🇰", "Sweden": "🇸🇪", "Norway": "🇳🇴",
    "Turkey": "🇹🇷", "Czech Republic": "🇨🇿", "Slovakia": "🇸🇰",
    "Romania": "🇷🇴", "Serbia": "🇷🇸", "Greece": "🇬🇷",
    "Slovenia": "🇸🇮", "Croatia": "🇭🇷", "Finland": "🇫🇮",
    "Ireland": "🇮🇪", "Iceland": "🇮🇸", "Israel": "🇮🇱",
    "Saudi Arabia": "🇸🇦", "Qatar": "🇶🇦", "Iran": "🇮🇷",
    "Ecuador": "🇪🇨", "Peru": "🇵🇪", "Chile": "🇨🇱",
    "Paraguay": "🇵🇾", "New Zealand": "🇳🇿",
}

WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "SportsAnnouncer/1.0 (github.com/sports-announcer)"}


class WikipediaFootballAPI:
    def __init__(self, days_ahead: int = 7, tz_offset: int = 3):
        self.days_ahead = days_ahead
        self.tz_offset = tz_offset
        self._last_request: Optional[datetime] = None

    def _rate_limit(self):
        now = datetime.now()
        if self._last_request and (now - self._last_request).total_seconds() < 2:
            time.sleep(2)
        self._last_request = now

    def get_upcoming_matches(self, competitions: Optional[List[Dict]] = None) -> List[Dict]:
        if competitions is None:
            competitions = [
                {"name": "UEFA Nations League", "page": "2026–27 UEFA Nations League"},
                {"name": "UEFA Europa League", "page": "2026–27 UEFA Europa League"},
                {"name": "UEFA Conference League", "page": "2026–27 UEFA Conference League"},
                {"name": "FIFA Club World Cup", "page": "2027 FIFA Club World Cup"},
            ]

        results: List[Dict] = []
        for comp in competitions:
            try:
                matches = self._fetch_competition_matches(comp["name"], comp["page"])
                results.extend(matches)
            except Exception:
                continue

        results.sort(key=lambda m: m.get("date") or "")
        return results

    def _fetch_competition_matches(self, comp_name: str, page_title: str) -> List[Dict]:
        html = self._get_page_html(page_title)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        today = datetime.now()
        cutoff = today + timedelta(days=self.days_ahead)
        matches: List[Dict] = []
        seen = set()

        tables = soup.find_all("table", class_="wikitable")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) < 3:
                    continue

                row_text = row.get_text(" ", strip=True)
                date_info = self._extract_date_from_row(row_text, cells)
                if not date_info:
                    continue

                date_str, date_obj = date_info
                if date_obj and (date_obj < today - timedelta(days=1) or date_obj > cutoff):
                    continue

                teams = self._extract_teams(row_text, cells)
                if not teams:
                    continue

                home, away = teams
                dedup_key = f"{date_str}|{home}|{away}"
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                matches.append({
                    "competition": comp_name,
                    "emblem": COMPETITION_EMOJIS.get(comp_name, "⚽"),
                    "home_team": home,
                    "away_team": away,
                    "home_flag": self._flag(home),
                    "away_flag": self._flag(away),
                    "date": date_str,
                    "venue": "",
                    "stage": self._extract_stage(row, table, soup),
                    "group": "",
                    "source": "wikipedia",
                })

        return matches

    def _get_page_html(self, title: str) -> Optional[str]:
        self._rate_limit()
        params = {
            "action": "parse",
            "page": title,
            "prop": "text",
            "format": "json",
            "redirects": 1,
        }
        try:
            r = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                return None
            data = r.json()
            if "error" in data:
                return None
            text_data = data.get("parse", {}).get("text", {})
            if not text_data:
                return None
            return list(text_data.values())[0]
        except requests.RequestException:
            return None

    def _extract_date_from_row(self, row_text: str, cells) -> Optional[Tuple[str, datetime]]:
        for cell in cells:
            text = cell.get_text(" ", strip=True)
            for month_name, month_num in MONTH_NAMES.items():
                pattern = rf"(\d{{1,2}})\s*{month_name}\s*(\d{{4}})?"
                m = re.search(pattern, text, re.IGNORECASE)
                if m:
                    day = int(m.group(1))
                    year = int(m.group(2)) if m.group(2) else datetime.now().year
                    if 1 <= day <= 31 and 2024 <= year <= 2030:
                        try:
                            dt = datetime(year, month_num, day)
                            local = dt + timedelta(hours=self.tz_offset)
                            return local.strftime("%d.%m.%Y"), dt
                        except ValueError:
                            continue
        return None

    def _extract_teams(self, row_text: str, cells) -> Optional[Tuple[str, str]]:
        text_links = []
        for cell in cells:
            for a in cell.find_all("a"):
                title = a.get("title", "") or a.get_text(strip=True)
                if title and len(title) > 2:
                    text_links.append(title)

        team_links = [t for t in text_links if self._is_team_name(t)]
        if len(team_links) >= 2:
            return team_links[0], team_links[1]

        text = row_text
        parts = re.split(r"\s*(?:v|vs\.?|–|—|×)\s*", text, maxsplit=1)
        if len(parts) == 2:
            home = parts[0].strip().split()[-1] if parts[0].strip() else ""
            away = parts[1].strip().split()[0] if parts[1].strip() else ""
            if home and away and len(home) > 2 and len(away) > 2:
                return home, away

        return None

    def _is_team_name(self, text: str) -> bool:
        if not text or len(text) < 3:
            return False
        skip = {"Edit", "Wikipedia", "Help", "Special", "Main Page", "File", "Template", "Category", "Portal", "Talk", "User"}
        if text in skip or any(text.startswith(s) for s in ["List of", "Template:", "Category:"]):
            return False
        if re.match(r"^\d", text):
            return False
        if any(kw in text.lower() for kw in ["round", "group", "matchday", "goal", "score", "referee", "attendance", "stadium"]):
            return False
        return True

    def _extract_stage(self, row, table, soup) -> str:
        caption = table.find("caption")
        if caption:
            text = caption.get_text(strip=True)
            if text:
                return text[:100]

        prev = table.find_previous(["h2", "h3", "h4"])
        if prev:
            text = prev.get_text(strip=True)
            text = re.sub(r"\[edit\]|\[edit\]", "", text).strip()
            if text and len(text) < 100:
                return text
        return ""

    def _flag(self, team_name: str) -> str:
        for key, flag in TEAM_FLAGS.items():
            if key.lower() in team_name.lower():
                return flag
        return ""
