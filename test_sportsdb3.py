import requests, json

# Try searchteams endpoint - it might find leagues too
BASE = "https://www.thesportsdb.com/api/v1/json/3"

searches = [
    "UEFA_Europa_League",
    "Europa_League",
    "UEFA_Conference",
    "Nations_League",
    "Club_World_Cup",
    "World_Cup",
]

for s in searches:
    r = requests.get(f"{BASE}/searchteams.php?t={s}", timeout=30)
    data = r.json()
    teams = data.get("teams", [])
    if teams:
        print(f"\n{s}: {len(teams)} results")
        for t in teams[:3]:
            print(f"  {t.get('idTeam','?')}: {t.get('strTeam','?')} (league: {t.get('idLeague','?')})")
    else:
        print(f"{s}: no results")

# Also try lookupleague for nearby IDs
def try_ids(start, end):
    for lid in range(start, end+1):
        try:
            r = requests.get(f"{BASE}/lookupleague.php?id={lid}", timeout=15)
            data = r.json()
            league = data.get("leagues", [])
            if league:
                name = league[0].get("strLeague", "?")
                sport = league[0].get("strSport", "?")
                print(f"  {lid}: {name} ({sport})")
        except:
            pass

print("\nScanning IDs 4440-4460...")
try_ids(4440, 4460)
print("\nScanning IDs 4460-4480...")
try_ids(4460, 4480)
print("\nScanning IDs 4490-4520...")
try_ids(4490, 4520)
print("\nScanning IDs 4530-4560...")
try_ids(4530, 4560)
