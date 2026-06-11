import requests, re
from bs4 import BeautifulSoup

r = requests.get(
    "https://liveball.sx/",
    timeout=30,
    headers={"User-Agent": "Mozilla/5.0"},
)
soup = BeautifulSoup(r.text, "html.parser")

# Look for match elements
# Find all elements with class containing "match"
for cls in ["match", "event", "game", "card", "row", "item", "schedule"]:
    elements = soup.find_all(class_=re.compile(cls, re.I))
    if elements:
        print(f"Class '{cls}': {len(elements)} elements")
        if len(elements) <= 5:
            for e in elements:
                print(f"  {e.get_text(strip=True)[:100]}")

# Find all links
links = soup.find_all("a", href=True)
print(f"\nTotal links: {len(links)}")
for a in links[:20]:
    href = a.get("href", "")
    text = a.get_text(strip=True)
    if text:
        print(f"  {text[:60]} -> {href}")

# Look for the schedule/match list specifically
schedules = soup.find_all("div", id=re.compile(r"schedule|matches|events|content", re.I))
print(f"\nRelevant divs: {len(schedules)}")
for s in schedules[:5]:
    print(f"  id={s.get('id','')} class={s.get('class','')}")
    text = s.get_text(strip=True)[:200]
    print(f"  text: {text}")
