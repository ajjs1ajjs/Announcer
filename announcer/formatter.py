from datetime import datetime
from typing import Dict, List


TEAM_FLAGS: Dict[str, str] = {}


def _team_flag(name: str) -> str:
    known = {
        "Brazil": "🇧🇷", "Argentina": "🇦🇷", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "Spain": "🇪🇸", "France": "🇫🇷", "Germany": "🇩🇪", "Italy": "🇮🇹",
        "Netherlands": "🇳🇱", "Portugal": "🇵🇹", "Uruguay": "🇺🇾",
        "Belgium": "🇧🇪", "Croatia": "🇭🇷", "Switzerland": "🇨🇭",
        "Colombia": "🇨🇴", "Mexico": "🇲🇽", "Ukraine": "🇺🇦",
        "Poland": "🇵🇱", "Hungary": "🇭🇺", "Austria": "🇦🇹",
        "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
        "USA": "🇺🇸", "Canada": "🇨🇦", "Japan": "🇯🇵", "South Korea": "🇰🇷",
        "Australia": "🇦🇺", "Nigeria": "🇳🇬", "Senegal": "🇸🇳",
        "Morocco": "🇲🇦", "Egypt": "🇪🇬", "Cameroon": "🇨🇲",
        "Ghana": "🇬🇭", "Algeria": "🇩🇿", "Tunisia": "🇹🇳",
        "Ivory Coast": "🇨🇮", "Mali": "🇲🇱", "Burkina Faso": "🇧🇫",
        "Denmark": "🇩🇰", "Sweden": "🇸🇪", "Norway": "🇳🇴",
        "Finland": "🇫🇮", "Ireland": "🇮🇪", "Turkey": "🇹🇷",
        "Czech Republic": "🇨🇿", "Slovakia": "🇸🇰", "Romania": "🇷🇴",
        "Bulgaria": "🇧🇬", "Serbia": "🇷🇸", "Greece": "🇬🇷",
        "Slovenia": "🇸🇮", "Montenegro": "🇲🇪", "North Macedonia": "🇲🇰",
        "Bosnia and Herzegovina": "🇧🇦", "Albania": "🇦🇱",
        "Iceland": "🇮🇸", "Israel": "🇮🇱", "Georgia": "🇬🇪",
        "Armenia": "🇦🇲", "Azerbaijan": "🇦🇿",
        "Saudi Arabia": "🇸🇦", "Qatar": "🇶🇦", "Iran": "🇮🇷",
        "Ecuador": "🇪🇨", "Peru": "🇵🇪", "Chile": "🇨🇱",
        "Paraguay": "🇵🇾", "Bolivia": "🇧🇴", "Venezuela": "🇻🇪",
        "Costa Rica": "🇨🇷", "Panama": "🇵🇦", "Honduras": "🇭🇳",
        "Jamaica": "🇯🇲", "Trinidad and Tobago": "🇹🇹",
        "New Zealand": "🇳🇿",
        "Real Madrid": "⚪", "Barcelona": "🔵🔴",
        "Bayern Munich": "🔴", "Manchester City": "🔵",
        "Manchester United": "🔴", "Liverpool": "🔴",
        "Paris Saint-Germain": "🔵🔴", "Inter Milan": "🔵⚫",
        "AC Milan": "🔴⚫", "Juventus": "⚫⚪",
        "Chelsea": "🔵", "Arsenal": "🔴", "Tottenham": "⚪",
    }
    for key, flag in known.items():
        if key.lower() in name.lower():
            return flag
    return ""


def _stage_label(match: Dict) -> str:
    stage = match.get("stage", "") or ""
    group = match.get("group", "") or ""
    parts = []
    if stage and stage != "REGULAR_SEASON":
        parts.append(stage.replace("_", " ").title())
    if group:
        parts.append(f"Group {group}")
    return " | ".join(parts) + ("\n" if parts else "")


def format_football_section(matches: List[Dict]) -> str:
    if not matches:
        return ""

    lines = ["<b>⚽️ ФУТБОЛЬНІ МАТЧІ</b>\n"]
    current_comp = None

    for m in matches:
        if m["competition"] != current_comp:
            current_comp = m["competition"]
            emblem = m.get("emblem", "⚽")
            lines.append(f"\n{emblem} <b>{current_comp}</b>")

        date = m.get("date", "???")
        home = m["home_team"]
        away = m["away_team"]
        home_flag = _team_flag(home)
        away_flag = _team_flag(away)
        stage_info = _stage_label(m)

        lines.append(
            f"\n  📅 {date}\n"
            f"  {home_flag} {home} vs {away_flag} {away}"
        )

        if stage_info:
            lines[-1] += f"\n  {stage_info.strip()}"

        venue = m.get("venue", "")
        if venue:
            lines[-1] += f"\n  📍 {venue}"

        lines[-1] += "\n  ─────────────────"

    return "\n".join(lines)


def format_boxing_section(events: List[Dict]) -> str:
    if not events:
        return ""

    lines = ["\n\n<b>🥊 БОКС — НАЙБЛИЖЧІ БОЇ</b>\n"]

    for ev in events[:10]:
        date = ev.get("date", "???")
        event_name = ev.get("event", "Бій")
        fighters = ev.get("fighters", [])
        location = ev.get("location", "")
        titles = ev.get("titles", "")

        lines.append(f"\n  📅 {date}")
        fighter_str = " vs ".join(fighters) if fighters else event_name
        lines.append(f"  🥊 {fighter_str}")

        if titles:
            lines[-1] += f"\n  🏅 {titles}"
        if location:
            lines[-1] += f"\n  📍 {location}"

        lines.append("  ─────────────────")

    return "\n".join(lines)


def format_daily_digest(football_matches: List[Dict], boxing_events: List[Dict]) -> str:
    today = datetime.now().strftime("%d.%m.%Y")
    header = f"<b>📢 СПОРТИВНИЙ ДАЙДЖЕСТ</b> | {today}\n{'═' * 30}"

    fb = format_football_section(football_matches)
    bx = format_boxing_section(boxing_events)

    if not fb and not bx:
        return f"{header}\n\nНа найближчі дні немає запланованих подій."

    if not fb:
        fb = "\n\n<b>⚽️ ФУТБОЛЬНІ МАТЧІ</b>\n\n  Немає запланованих матчів."
    if not bx:
        bx = ""

    return f"{header}{fb}{bx}"


def split_message(text: str, max_len: int = 4000) -> List[str]:
    if len(text) <= max_len:
        return [text]

    parts = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > max_len:
            parts.append(current)
            current = line
        else:
            current += "\n" + line if current else line

    if current:
        parts.append(current)

    return parts
