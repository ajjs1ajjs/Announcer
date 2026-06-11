import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests


MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}


class BoxingAPI:
    WIKI_API = "https://en.wikipedia.org/w/api.php"
    HEADERS = {"User-Agent": "SportsAnnouncer/1.0 (https://github.com/sports-announcer; contact@example.com)"}

    def __init__(self, days_ahead: int = 7):
        self._pages_cache: Optional[tuple[datetime, List[str]]] = None
        self._max_retries = 2
        self.days_ahead = days_ahead

    def get_upcoming_events(self) -> List[Dict]:
        fight_titles = self._get_fight_pages()
        if not fight_titles:
            return []

        extracts = self._get_extracts(fight_titles)
        events = []

        for title, extract in extracts:
            info = self._parse_fight_info(title, extract)
            if info and info["is_upcoming"]:
                events.append(info)

        events.sort(key=lambda e: e.get("_sort_date", "9999-99-99"))
        return events[:10]

    def _request(self, params: Dict) -> Optional[Dict]:
        for attempt in range(self._max_retries):
            try:
                resp = requests.get(self.WIKI_API, params=params, headers=self.HEADERS, timeout=10)
                resp.raise_for_status()
                return resp.json()
            except (requests.RequestException, ValueError):
                if attempt < self._max_retries - 1:
                    time.sleep(1)
        return None

    def _get_fight_pages(self) -> List[str]:
        now = datetime.now()
        if self._pages_cache and (now - self._pages_cache[0]) < timedelta(hours=1):
            return self._pages_cache[1]

        data = self._request({
            "action": "query",
            "list": "categorymembers",
            "cmtitle": "Category:2026_boxing_matches",
            "format": "json",
            "cmlimit": "50",
        })
        if not data:
            return []

        pages = data.get("query", {}).get("categorymembers", [])
        titles = [p["title"] for p in pages if p.get("ns") == 0]
        if titles:
            self._pages_cache = (now, titles)
        return titles

    def _get_extracts(self, titles: List[str]) -> List[tuple[str, str]]:
        titles_str = "|".join(titles[:25])
        data = self._request({
            "action": "query",
            "titles": titles_str,
            "prop": "extracts|info",
            "exintro": 1,
            "explaintext": 1,
            "format": "json",
        })
        if not data:
            return [(t, "") for t in titles]

        results = []
        for page in data.get("query", {}).get("pages", {}).values():
            title = page.get("title", "")
            extract = page.get("extract", "") or ""
            results.append((title, extract))
        return results

    def _parse_fight_info(self, title: str, extract: str) -> Optional[Dict]:
        if not title:
            return None

        fighters = self._extract_fighters(title)
        date_str, date_obj = self._extract_date(extract)
        is_upcoming = self._is_upcoming(extract)

        if date_obj and date_obj < datetime.now() - timedelta(days=1):
            is_upcoming = False
        if date_obj and date_obj > datetime.now() + timedelta(days=self.days_ahead):
            is_upcoming = False

        titles_str = self._extract_titles(extract)
        location = self._extract_location(extract)

        return {
            "date": date_str or "TBD",
            "event": title,
            "fighters": fighters,
            "location": location,
            "titles": titles_str,
            "is_upcoming": is_upcoming,
            "source": "wikipedia",
            "_sort_date": date_obj.strftime("%Y-%m-%d") if date_obj else "9999-99-99",
        }

    def _extract_fighters(self, title: str) -> List[str]:
        parts = re.split(r"\s+vs\.?\s+", title, maxsplit=1)
        if len(parts) != 2:
            return [title]
        fighters = []
        for p in parts:
            name = p.strip()
            name = re.sub(r'\s+(II|III|IV|V|VI|VII|VIII|IX|X)$', '', name)
            fighters.append(name.strip())
        return fighters

    def _extract_date(self, text: str) -> tuple[Optional[str], Optional[datetime]]:
        patterns = [
            r"(?:take place|took place|scheduled for|set for)\s+on\s+(\w+\s+\d{1,2},?\s*\d{4})",
            r"(?:take place|took place|scheduled for|set for)\s+on\s+(\w+\s+\d{1,2})",
            r"on\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s*(\d{4})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    month_str, day_str, year_str = groups
                    date_str = f"{month_str} {day_str}, {year_str}"
                else:
                    date_str = groups[0]
                date_obj = self._str_to_date(date_str)
                return date_str, date_obj
        return None, None

    def _str_to_date(self, date_str: str) -> Optional[datetime]:
        try:
            cleaned = date_str.strip().replace(",", "")
            parts = cleaned.split()
            if len(parts) >= 2:
                month = MONTH_MAP.get(parts[0].lower())
                day = int(parts[1])
                year = int(parts[2]) if len(parts) >= 3 else datetime.now().year
                if month:
                    return datetime(year, month, day)
        except (ValueError, IndexError):
            pass
        return None

    def _is_upcoming(self, text: str) -> bool:
        if not text:
            return False
        tl = text.lower()
        if "upcoming" in tl or "scheduled to take place" in tl:
            return True
        past_words = ["took place", "was a ", "was held", "defeated", "resulted", "won by"]
        if any(w in tl for w in past_words):
            return False
        return False

    def _extract_titles(self, text: str) -> str:
        patterns = [
            r"((?:WBC|WBA|IBF|WBO|The Ring)\s+(?:\w+\s+){0,4}(?:champion|title|belt))",
            r"((?:\w+\s+)?-?\s*division\s+world\s+champion)",
        ]
        found = set()
        for p in patterns:
            for m in re.findall(p, text, re.IGNORECASE):
                mc = m.strip()
                if len(mc) > 3:
                    found.add(mc)
        return "; ".join(sorted(found)[:3]) if found else ""

    def _extract_location(self, text: str) -> str:
        m = re.search(r"at\s+([A-Za-z0-9\s.'-]+?)(?:\s+in\s+([A-Za-z\s'-]+))?(?:\s*[,\.])", text)
        if m:
            parts = [p.strip() for p in m.groups() if p]
            return ", ".join(parts)
        return ""
