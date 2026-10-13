"""Scan every configured careers source and list unseen research-type postings.

Usage: python3 -I scan.py [tracker_ids.txt]
Skips ids in seen.json, rejected.json and the optional tracker id list.
Writes candidates.json (unseen postings with titles that look like research roles)
and prints a coverage table: source, HTTP status, total postings, candidates.
"""
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request

ASHBY = ["lumaai", "worldlabs", "genmo", "krea", "odysseyml", "hedra", "pika", "applied",
         "mirage", "physicalintelligence", "runway", "openai", "synthesia", "midjourney"]
GREENHOUSE = ["waymo", "kodiak", "nuro", "stabilityai", "xai", "anthropic", "heygen", "figureai"]
WORKDAY = {
    "NVIDIA": "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs",
    "Adobe": "https://adobe.wd5.myworkdayjobs.com/wday/cxs/adobe/external_experienced/jobs",
}
QUERIES = ["research scientist video", "research scientist 3D", "research scientist generative",
           "world model", "neural rendering", "research scientist computer vision"]

TITLE_OK = re.compile(r"research|scientist|researcher|member of technical staff|\bmts\b|machine learning|"
                      r"\bml\b|applied scientist|world model|generative|vision|3d|video|graphics", re.I)
TITLE_BAD = re.compile(r"intern\b|internship|principal|director|manager|\bhead of|recruit|sales|"
                       r"account|counsel|legal|finance|marketing|technician|hardware|firmware|"
                       r"\bstaff\b(?! research)|postdoc", re.I)
NON_US = re.compile(r"london|toronto|vancouver|montreal|beijing|shanghai|shenzhen|hangzhou|singapore|"
                    r"tokyo|seoul|paris|berlin|munich|zurich|freiburg|amsterdam|dublin|tel aviv|"
                    r"bangalore|bengaluru|hyderabad|sydney|uk\b|united kingdom|canada|germany|china|india|japan", re.I)


def norm_id(url):
    u = url.strip().split("#")[0].rstrip("/")
    return hashlib.sha1(u.encode()).hexdigest()[:16]


def get(url, data=None, headers=None):
    h = {"User-Agent": "Mozilla/5.0", **(headers or {})}
    body = json.dumps(data).encode() if data is not None else None
    if body:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=h)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read().decode("utf-8", "replace")


def ashby(org):
    _, t = get(f"https://api.ashbyhq.com/posting-api/job-board/{org}")
    for j in json.loads(t)["jobs"]:
        yield org, j["title"], j.get("location", ""), j["jobUrl"], (j.get("publishedAt") or "")[:10]


def greenhouse(org):
    _, t = get(f"https://boards-api.greenhouse.io/v1/boards/{org}/jobs")
    for j in json.loads(t)["jobs"]:
        yield org, j["title"], (j.get("location") or {}).get("name", ""), j["absolute_url"], (j.get("updated_at") or "")[:10]


def workday(name, api):
    # https://HOST/wday/cxs/TENANT/SITE/jobs -> public pages live at https://HOST/SITE<externalPath>
    host, rest = api.split("/wday/cxs/")
    public = f"{host}/{rest.split('/')[1]}"
    seen = set()
    for q in QUERIES:
        _, t = get(api, {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": q})
        for j in json.loads(t).get("jobPostings", []):
            if j["externalPath"] in seen:
                continue
            seen.add(j["externalPath"])
            yield name, j["title"], j.get("locationsText", ""), public + j["externalPath"], j.get("postedOn", "")


def apple():
    seen = set()
    for q in QUERIES:
        url = "https://jobs.apple.com/en-us/search?location=united-states-USA&search=" + urllib.parse.quote(q)
        _, t = get(url)
        for path in re.findall(r"/en-us/details/[0-9]+-[0-9]+/[a-z0-9-]+", t):
            key = path.split("/")[3].split("-")[0]
            if key in seen:
                continue
            seen.add(key)
            yield "Apple", path.rsplit("/", 1)[1].replace("-", " "), "US", "https://jobs.apple.com" + path, ""


def google():
    seen = set()
    for q in QUERIES:
        url = ("https://www.google.com/about/careers/applications/jobs/results/?location=United%20States&q="
               + urllib.parse.quote(q))
        _, t = get(url)
        for path in re.findall(r"jobs/results/[0-9]+-[a-z0-9-]+", t):
            if path in seen:
                continue
            seen.add(path)
            yield "Google", path.split("-", 1)[1].replace("-", " "), "US", \
                "https://www.google.com/about/careers/applications/" + path, ""


def tiktok():
    seen = set()
    for q in QUERIES:
        _, t = get("https://api.lifeattiktok.com/api/v1/public/supplier/search/job/posts",
                   {"keyword": q, "limit": 50, "offset": 0, "job_category_id_list": [],
                    "location_code_list": [], "subject_id_list": [], "recruitment_id_list": []},
                   {"website-path": "tiktok"})
        for j in (json.loads(t).get("data") or {}).get("job_post_list", []):
            if j["id"] in seen:
                continue
            seen.add(j["id"])
            city = (j.get("city_info") or {}).get("en_name", "")
            yield "TikTok", j["title"], city, f"https://lifeattiktok.com/search/{j['id']}", ""


def main():
    seen = set(json.load(open("seen.json")))
    try:  # ids already reviewed and turned down on an earlier day
        seen |= set(json.load(open("rejected.json")))
    except FileNotFoundError:
        pass
    if len(sys.argv) > 1:
        seen |= {l.strip() for l in open(sys.argv[1]) if l.strip()}
    sources = ([(f"ashby:{o}", lambda o=o: ashby(o)) for o in ASHBY]
               + [(f"greenhouse:{o}", lambda o=o: greenhouse(o)) for o in GREENHOUSE]
               + [(f"workday:{n}", lambda n=n, a=a: workday(n, a)) for n, a in WORKDAY.items()]
               + [("apple", apple), ("google", google), ("tiktok", tiktok)])
    out, rows = [], []
    for name, fn in sources:
        try:
            jobs = list(fn())
            status = "ok"
        except Exception as e:  # one broken source must not stop the scan
            jobs, status = [], f"ERROR {type(e).__name__}: {str(e)[:60]}"
        cand = [j for j in jobs
                if TITLE_OK.search(j[1]) and not TITLE_BAD.search(j[1])
                and not NON_US.search(j[2] or "") and not NON_US.search(j[3].split("/job/")[-1][:40]) and norm_id(j[3]) not in seen]
        for org, title, loc, url, posted in cand:
            out.append({"source": name, "company": org, "title": title, "location": loc,
                        "url": url, "posted": posted, "id": norm_id(url)})
        rows.append((name, status, len(jobs), len(cand)))
    json.dump(out, open("candidates.json", "w"), indent=1, ensure_ascii=False)
    print(f"{'source':28} {'status':10} {'total':>6} {'new':>5}")
    for r in rows:
        print(f"{r[0]:28} {r[1][:40]:10} {r[2]:>6} {r[3]:>5}")
    print(f"\n{len(out)} unseen candidates -> candidates.json")


if __name__ == "__main__":
    main()
