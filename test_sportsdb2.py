import requests, json

BASE = "https://www.thesportsdb.com/api/v1/json/3"

# Known UEFA competition IDs
ids = {
    4480: "UEFA Champions League",
    4449: "UEFA Europa League",
    4502: "UEFA Conference League",
    4548: "UEFA Nations League",
    4642: "UEFA Nations League (alt)",
    4331: "FIFA Club World Cup",
}

for lid, name in ids.items():
    r = requests.get(f"{BASE}/lookupleague.php?id={lid}", timeout=30)
    data = r.json()
    league = data.get("leagues", [])
    if league:
        print(f"{lid}: {name} -> FOUND: {league[0].get('strLeague', '?')}")
    else:
        print(f"{lid}: {name} -> NOT FOUND")
