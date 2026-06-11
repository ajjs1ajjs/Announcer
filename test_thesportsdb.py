import requests

BASE = "https://www.thesportsdb.com/api/v1/json/3"

# Try searching for each league with longer timeout
targets = [
    "UEFA Nations League",
    "UEFA Europa League",
    "UEFA Conference League",
    "FIFA Club World Cup",
]

for t in targets:
    try:
        r = requests.get(f"{BASE}/searchteams.php?t={t}", timeout=30)
    except Exception as e:
        print(f"{t}: ERROR {e}")

    try:
        r = requests.get(f"{BASE}/searchteams.php?t={t.replace(' ', '_')}", timeout=30)
    except Exception as e:
        print(f"{t}: ERROR {e}")

# Let's look up known IDs from documentation
# Try looking up by specific league names
for t in targets:
    try:
        r = requests.get(f"{BASE}/searchteams.php?t={t.replace(' ', '_')}", timeout=30)
        print(f"searchteams({t}): {r.status_code}")
        data = r.json()
        print(f"  Keys: {list(data.keys())}")
    except Exception as e:
        print(f"searchteams({t}): ERROR {e}")
