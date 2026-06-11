import requests, re, json

r = requests.get(
    "https://liveball.sx/",
    timeout=30,
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
)
text = r.text
print(f"Page size: {len(text)} chars")

# Search for scripts that contain JSON data
scripts = re.findall(r"<script[^>]*>(.*?)</script>", text, re.DOTALL)
print(f"Found {len(scripts)} scripts")
for i, s in enumerate(scripts):
    s_clean = s.strip()
    if len(s_clean) > 100 and ("match" in s_clean.lower() or "football" in s_clean.lower() or "schedule" in s_clean.lower() or "event" in s_clean.lower()):
        print(f"\nScript {i}: {len(s_clean)} chars")
        print(s_clean[:300])
        if len(s_clean) <= 500:
            print(s_clean)
