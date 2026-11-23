"""Refresh public/data/youtube.json with the latest Shorts from each channel's public RSS feed.
Runs from GitHub Actions; no API key needed."""
import json, re, urllib.request, http.client, datetime, xml.etree.ElementTree as ET
PATH = "public/data/youtube.json"
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "media": "http://search.yahoo.com/mrss/"}
KEEP = 8

def is_short(vid):
    # youtube.com/shorts/ID answers 200 for a Short and redirects for a regular video
    c = http.client.HTTPSConnection("www.youtube.com", timeout=15)
    c.request("HEAD", f"/shorts/{vid}", headers={"User-Agent": "Mozilla/5.0"})
    s = c.getresponse().status
    c.close()
    return s == 200

data = json.load(open(PATH, encoding="utf-8"))
for key, ch in data["channels"].items():
    try:
        req = urllib.request.Request(f"https://www.youtube.com/feeds/videos.xml?channel_id={ch['id']}", headers={"User-Agent": "Mozilla/5.0"})
        root = ET.fromstring(urllib.request.urlopen(req, timeout=20).read())
    except Exception as e:
        print(f"{key}: feed failed, keeping current list ({e})")
        continue
    vids = []
    for en in root.findall("a:entry", NS):
        vid = en.find("yt:videoId", NS).text
        title = re.sub(r"\s*#shorts?\b", "", en.find("a:title", NS).text or "", flags=re.I).strip()
        try:
            if not is_short(vid):
                continue
        except Exception:
            pass
        vids.append({"id": vid, "title": title, "published": en.find("a:published", NS).text})
        if len(vids) >= KEEP:
            break
    if vids:
        ch["videos"] = vids
        print(f"{key}: {len(vids)} shorts")
data["updated"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")
json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
