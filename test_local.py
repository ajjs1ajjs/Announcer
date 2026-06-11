import sys, json
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from announcer.football import FootballAPI
from announcer.config import Config

cfg = Config(
    "bbb39e45edba41b9be3c7f89bfde58c2",
    "7336475367:AAGPDDUC4IdopHjOhBc9-T83b52Gj1OjBvg",
    "-1003903136690",
    timezone_offset=3,
    days_ahead=7,
)
m = FootballAPI(cfg).get_upcoming_matches()
print(f"Matches: {len(m)}")
for x in m:
    print(f'{x["date"]}  {x["home_team"]} vs {x["away_team"]}  [{x["competition"]}]')
