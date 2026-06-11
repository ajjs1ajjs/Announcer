import requests, json

r = requests.get("https://www.thesportsdb.com/api/v1/json/3/all_leagues.php", timeout=120)
data = r.json()
leagues = data.get("leagues", [])
for l in leagues:
    print(f'  {l["idLeague"]}: {l["strLeague"]} ({l.get("strSport","")})')
