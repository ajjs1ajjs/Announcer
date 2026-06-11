import sys, requests
from datetime import datetime, timedelta, timezone

key = "bbb39e45edba41b9be3c7f89bfde58c2"
headers = {"X-Auth-Token": key}

today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
until = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")
print(f"Date range: {today} to {until}")

# Comps with codes
comp_codes = ["WC", "EC", "CL", "PL", "ELC", "BSA", "FL1", "BL1", "SA", "DED", "PPL", "PD", "CLI"]
for code in comp_codes:
    r = requests.get(
        f"https://api.football-data.org/v4/competitions/{code}/matches",
        headers=headers,
        params={"dateFrom": today, "dateTo": until, "status": "SCHEDULED,TIMED"},
        timeout=15
    )
    if r.status_code != 200:
        continue
    matches = r.json().get("matches", [])
    if matches:
        print(f"\n{code}: {len(matches)} matches")
        for m in matches:
            print(f"  {m.get('utcDate','')} - {m['homeTeam']['name']} vs {m['awayTeam']['name']}")
    else:
        print(f"{code}: 0 matches")
