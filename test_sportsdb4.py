import requests, json

# Try different API versions
for ver in ["1", "2", "3"]:
    r = requests.get(f"https://www.thesportsdb.com/api/v1/json/{ver}/all_leagues.php", timeout=120)
    data = r.json()
    leagues = data.get("leagues", [])
    soccer = [l for l in leagues if l.get("strSport", "").lower() == "soccer"]
    print(f"v{ver}: {len(leagues)} total, {len(soccer)} soccer")
    for l in soccer:
        name = l.get("strLeague", "")
        print(f"  {l['idLeague']}: {name}")
